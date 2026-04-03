# Időskori eséskockázat predikciója a talpnyomásközéppont jellemzőinek gépi tanulás alapú elemzésével

Ez a repozitórium a szakdolgozatom keretein belül készült kódokat tartalmazza.

## Kutatasi_terv.pdf
A dolgozat kutatási terve.

## Video_vago.py
A talpnyomáseloszlásról készült 60 másodperces felvételek első 10, valamint utolsó 5 másodpercét levágja, hogy a dinamikus mozgások ne befolyásolják az eredményeket.

## Elofeldolgozas.py
Ez a program végzi az adatok előfeldolgozását. Iteratívan beolvassa a nyers mérési eredményeket, ezeket szűri, görbéket illeszt rá, majd számos CoP jellemzőt számol.

## Modellek.ipynb
Ez a program felelős a gépi tanulási modellek tanításáért. Beolvassa az adatokat, ellenőrzi a hiányzó adatokat, statisztikai elemzést végez rajtuk, majd 8 különböző gépi tanulási modellt hoz létre. Ezek teljesítményét számszerűsíti és ábrákat készít.
