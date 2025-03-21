# 🖧  ChatSSH

ChatSSH es una actividad escolar cuya finalidad es ayudar a una persona ficticia a controlar su Ciber. 

Mediante una página web hosteada en un droplet de Digital Ocean tendrá botones para apagar computadores al instante o mediante un temporizador.

## 🐍 Lenguajes utilizados
El lenguaje de programación utilizado fue Python, debido a sus librerías y facilidad de entender. Se utilizo html, css y js para el "frontend" de la página.

### 🎨 HTML, CSS, JavaScript
HTML, CSS y JavaScript son lenguajes de programación que se usan para desarrollar páginas web. HTML defina la estructura, CSS el diseño y JavaScript la interactividad.

- HTML: Define la estructrua básica de un sitio web.
- CSS: Se usa para controlar la presentación, el formato y el diseño
- JavaScript: Se usa para controlar el comportamiento de diferentes elementos.

### 🕮  Librerías 
Las librerías utilizadas están documentadas en el documento "requirements.txt". Todas las librerías del código son las siguientes:

#### 🖧  Flask
Flask es un framework minimalista escrito en Python que permite crear aplicaciones web rápidamente y con un mínimo número de líneas de código. Esta basado en la especificación WSGI de Werkzeug y el motor de templates Jinja2 y tiene una licencia BSD

<pre><code>	import os
	import paramiko
	import threading
	import time
	from flask import Flask, render_template, request, redirect, url_for, jsonify
</code></pre>


## 📋 Referencias
- [HTML, CSS y JavaScript](https://www.digitalhouse.com/blog/html-css-y-javascript-para-que-sirve-cada-lenguaje/)
- [Flask](https://es.wikipedia.org/wiki/Flask)
