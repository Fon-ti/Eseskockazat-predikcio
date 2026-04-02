import pandas as pd
import numpy as np
import os
from scipy.signal import butter, filtfilt
from scipy.interpolate import LSQUnivariateSpline

# ==========================================
# BEÁLLÍTÁSOK
# ==========================================
ROOT_SEARCH_DIR = r"K:\0 Szakdolgozat\adatok" 

STANCE_WIDTH_MM = 300.0  
Fs = 100            
CUTOFF_FREQ = 10    
ORDER = 4           
SLICE_DURATION = 1.0 
DECIMALS = 4        

FILENAME_COP = "Talp_CoPkoordinatai.txt"
FILENAME_FORCE = "Talp_eredoero.txt"

# ==========================================
# FÜGGVÉNYEK
# ==========================================

def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

def fit_thesis_spline(time, signal, slice_duration):
    if len(time) == 0: return signal
    start_time = time[0]
    end_time = time[-1]
    if end_time < slice_duration * 2:
        return signal
    knots = np.arange(start_time + slice_duration, end_time, slice_duration)
    try:
        spline = LSQUnivariateSpline(time, signal, t=knots, k=3)
        return spline(time)
    except:
        return signal

def load_folder_data(folder_path):
    path_cop = os.path.join(folder_path, FILENAME_COP)
    path_force = os.path.join(folder_path, FILENAME_FORCE)
    
    if not os.path.exists(path_cop) or not os.path.exists(path_force):
        # Hibakeresés: kiírjuk, ha nem találja a fájlt
        # print(f"    [HIBA] Nem találom a fájlokat itt: {folder_path}")
        return None

    try:
        df_c = pd.read_csv(path_cop, sep=None, engine='python')
        df_f = pd.read_csv(path_force, sep=None, engine='python')
        df_c.columns = df_c.columns.str.strip()
        df_f.columns = df_f.columns.str.strip()
        
        df_c = df_c.interpolate().ffill().bfill()
        df_f = df_f.interpolate().ffill().bfill()
        
        n = min(len(df_c), len(df_f))
        
        col_ml = [c for c in df_c.columns if 'ML' in c][0]
        col_ap = [c for c in df_c.columns if 'AP' in c][0]
        col_fz = [c for c in df_f.columns if 'Eredő' in c or 'Force' in c][0]
        
        return {
            'ML': df_c[col_ml].iloc[:n].values,
            'AP': df_c[col_ap].iloc[:n].values,
            'Fz': df_f[col_fz].iloc[:n].values
        }
    except Exception as e:
        print(f"    [HIBA] Fájl olvasási hiba: {e}")
        return None

def process_subject(bal_data, jobb_data, output_folder, subject_id):
    n = min(len(bal_data['ML']), len(jobb_data['ML']))
    time = np.arange(n) / Fs
    
    # 1. TRANSZFORMÁCIÓ (Bal láb tükrözés)
    offset = STANCE_WIDTH_MM / 2
    l_ml_glob = (-1 * bal_data['ML'][:n]) - offset
    r_ml_glob = jobb_data['ML'][:n] + offset
    
    # 2. NET COP
    total_fz = bal_data['Fz'][:n] + jobb_data['Fz'][:n]
    total_fz[total_fz == 0] = 1.0
    
    net_ml_raw = (l_ml_glob * bal_data['Fz'][:n] + r_ml_glob * jobb_data['Fz'][:n]) / total_fz
    net_ap_raw = (bal_data['AP'][:n] * bal_data['Fz'][:n] + jobb_data['AP'][:n] * jobb_data['Fz'][:n]) / total_fz
    
    # 3. SZŰRÉS + SPLINE
    net_ml_filt = butter_lowpass_filter(net_ml_raw, CUTOFF_FREQ, Fs, ORDER)
    net_ap_filt = butter_lowpass_filter(net_ap_raw, CUTOFF_FREQ, Fs, ORDER)
    
    pos_ml = fit_thesis_spline(time, net_ml_filt, SLICE_DURATION)
    pos_ap = fit_thesis_spline(time, net_ap_filt, SLICE_DURATION)
    
    # 4. VÁLTOZÓK
    vel_ml = np.gradient(pos_ml, 1/Fs); acc_ml = np.gradient(vel_ml, 1/Fs)
    vel_ap = np.gradient(pos_ap, 1/Fs); acc_ap = np.gradient(vel_ap, 1/Fs)
    
    avgML, avgAP = np.mean(pos_ml), np.mean(pos_ap)
    X_cent, Y_cent = pos_ml - avgML, pos_ap - avgAP
    R_i = np.sqrt(X_cent**2 + Y_cent**2)
    total_time = time[-1] - time[0]
    
    hosszML = np.sum(np.abs(np.diff(pos_ml)))
    hosszAP = np.sum(np.abs(np.diff(pos_ap)))
    teljeshossz = np.sum(np.sqrt(np.diff(pos_ml)**2 + np.diff(pos_ap)**2))
    
    cov_matrix = np.cov(pos_ml, pos_ap)
    lambda_vals, _ = np.linalg.eig(cov_matrix)
    ellipse_area_95 = np.pi * np.sqrt(np.abs(lambda_vals[0])) * np.sqrt(np.abs(lambda_vals[1])) * 5.991
    
    cross_prod = np.abs(X_cent[:-1] * Y_cent[1:] - X_cent[1:] * Y_cent[:-1])
    Sway_Area_Per_Sec = np.sum(cross_prod) / (2 * total_time)
    
    rmsX, rmsY = np.std(pos_ml), np.std(pos_ap)
    cov_xy = np.mean(X_cent * Y_cent)
    Sway_Dir_Coeff = cov_xy / (rmsX * rmsY) if (rmsX*rmsY) != 0 else 0
    
    # 5. SZIMMETRIA
    l_ml_f = butter_lowpass_filter((-1 * bal_data['ML'][:n]), CUTOFF_FREQ, Fs, ORDER)
    r_ml_f = butter_lowpass_filter(jobb_data['ML'][:n], CUTOFF_FREQ, Fs, ORDER)
    l_ap_f = butter_lowpass_filter(bal_data['AP'][:n], CUTOFF_FREQ, Fs, ORDER)
    r_ap_f = butter_lowpass_filter(jobb_data['AP'][:n], CUTOFF_FREQ, Fs, ORDER)
    
    corr_ml = np.corrcoef(l_ml_f, r_ml_f)[0, 1]
    corr_ap = np.corrcoef(l_ap_f, r_ap_f)[0, 1]
    
    # 6. MENTÉS
    stats_data = [
        ('avgML', avgML, 'mm'), ('avgAP', avgAP, 'mm'),
        ('avgX', np.mean(np.abs(X_cent)), 'mm'), ('avgY', np.mean(np.abs(Y_cent)), 'mm'), ('avgR', np.mean(R_i), 'mm'),
        ('maxabsX', np.max(np.abs(X_cent)), 'mm'), ('maxabsY', np.max(np.abs(Y_cent)), 'mm'), ('maxR', np.max(R_i), 'mm'),
        ('ampX', np.ptp(pos_ml), 'mm'), ('ampY', np.ptp(pos_ap), 'mm'),
        ('rmsX', rmsX, 'mm'), ('rmsY', rmsY, 'mm'), ('rmsR', np.sqrt(np.mean(R_i**2)), 'mm'),
        ('hosszML', hosszML, 'mm'), ('hosszAP', hosszAP, 'mm'), ('teljeshossz', teljeshossz, 'mm'),
        ('vML', hosszML/total_time, 'mm/s'), ('vAP', hosszAP/total_time, 'mm/s'), ('v', teljeshossz/total_time, 'mm/s'),
        ('ML_Peak_Vel', np.max(np.abs(vel_ml)), 'mm/s'), ('AP_Peak_Vel', np.max(np.abs(vel_ap)), 'mm/s'),
        ('ML_Peak_Acc', np.max(np.abs(acc_ml)), 'mm/s^2'), ('AP_Peak_Acc', np.max(np.abs(acc_ap)), 'mm/s^2'),
        ('ML_RMS_Acc', np.sqrt(np.mean(acc_ml**2)), 'mm/s^2'), ('AP_RMS_Acc', np.sqrt(np.mean(acc_ap**2)), 'mm/s^2'),
        ('Confidence_Ellipse_Area', ellipse_area_95, 'mm^2'),
        ('Sway_Area_Per_Sec', Sway_Area_Per_Sec, 'mm^2/s'),
        ('Sway_Dir_Coeff', Sway_Dir_Coeff, '-'),
        ('Phase_Plane_ML', np.sqrt(rmsX**2 + np.std(vel_ml)**2), '-'),
        ('Phase_Plane_AP', np.sqrt(rmsY**2 + np.std(vel_ap)**2), '-'),
        ('Planar_Deviation', rmsX + rmsY, 'mm'),
        ('Symmetry_Corr_ML', corr_ml, '-'),
        ('Symmetry_Corr_AP', corr_ap, '-')
    ]
    
    out_file = os.path.join(output_folder, f"Net_CoP_Global_Statistics_{subject_id}.txt")
    pd.DataFrame(stats_data, columns=['Parameter', 'Value', 'Unit']).round(DECIMALS).to_csv(out_file, index=False, sep='\t')
    print(f"  [OK] Eredmények mentve: {os.path.basename(out_file)}")

# ==========================================
# FŐ CIKLUS - SZIGORÚ MÓDSZER
# ==========================================

print(f"--- FELDOLGOZÁS INDÍTÁSA ---")
print(f"Gyökérkönyvtár: {ROOT_SEARCH_DIR}")

if not os.path.exists(ROOT_SEARCH_DIR):
    print("HIBA: A gyökérkönyvtár nem létezik!")
else:
    # 1. Mappák listázása a gyökérben
    subfolders = [f.name for f in os.scandir(ROOT_SEARCH_DIR) if f.is_dir()]
    print(f"Talált mappák ({len(subfolders)} db): {subfolders}")
    
    processed_count = 0
    
    for subject_id in subfolders:
        # Minden mappa egy ALANY (pl. "s01")
        subject_path = os.path.join(ROOT_SEARCH_DIR, subject_id)
        
        # Feltételezzük a fix struktúrát:
        # s01 -> s01_bal
        # s01 -> s01_jobb
        
        dir_bal_name = f"{subject_id}_bal"
        dir_jobb_name = f"{subject_id}_jobb"
        
        path_bal = os.path.join(subject_path, dir_bal_name)
        path_jobb = os.path.join(subject_path, dir_jobb_name)
        
        print(f"\nVizsgálom: {subject_id} ...")
        
        if os.path.exists(path_bal) and os.path.exists(path_jobb):
            print(f"  -> Bal és Jobb mappa megtalálva.")
            
            bal_data = load_folder_data(path_bal)
            jobb_data = load_folder_data(path_jobb)
            
            if bal_data and jobb_data:
                process_subject(bal_data, jobb_data, subject_path, subject_id)
                processed_count += 1
            else:
                print("  -> [HIBA] A txt fájlok hiányoznak vagy hibásak.")
        else:
            print(f"  -> [SKIP] Nem található a '{dir_bal_name}' vagy '{dir_jobb_name}' mappa.")

    print(f"\n--- VÉGE. Sikeresen feldolgozva: {processed_count} db alany. ---")