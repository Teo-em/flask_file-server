import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/x-icon')

@app.route('/', methods=['GET', 'POST'])
@app.route('/directory/', methods=['GET', 'POST'])
@app.route('/directory/<path:cdir>', methods=['GET', 'POST'])
def upload_file(cdir=''):
    pathdir = app.config['UPLOAD_FOLDER']
    back = ""
    if cdir:
        pathdir = os.path.join(pathdir, cdir+'/')
        back = os.path.dirname(os.path.dirname(cdir))
    errors = []
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                errors.append('No se puede crear un archivo sin nombre.')
            else:
                filename = secure_filename(file.filename)
                path = os.path.join(pathdir, filename)
                if os.path.exists(path):
                    errors.append('Ya existe un archivo con el mismo nombre.')
                else:
                    file.save(path)
        elif 'new_folder' in request.form:
            if request.form['new_folder'] == '':
                errors.append('No se puede crear un directorio sin nombre.')
            else:
                dname = secure_filename(request.form['new_folder'])
                path = os.path.join(pathdir, dname)
                if os.path.exists(path):
                    errors.append('Ya existe un directorio con el mismo nombre.')
                else:
                    os.mkdir(path)
        else:
            errors.append('No se ha especificado una acción.')

    for error in errors:
        flash(error)

    statvfs = os.statvfs(app.config['UPLOAD_FOLDER'])
    totalgb = (statvfs.f_frsize * statvfs.f_blocks)/1024/1024/1024
    freegb = (statvfs.f_frsize * statvfs.f_bfree)/1024/1024/1024
    taken = "{:.2f}".format(totalgb - freegb) + " GB"
    totalgb = "{:.2f}".format(totalgb) + " GB"
    files = []
    folders = []
    filenames = os.listdir(pathdir)
    for name in filenames:
        path = os.path.join(pathdir, name)
        if os.path.isfile(path):
            details = os.stat(path)
            size = details.st_size
            if size / (1024 * 1024) > 1:
                size = str("{:.2f}".format(size / (1024 * 1024))) + " mb"
            else:
                size = str("{:.2f}".format(size / 1024)) + " kb"
            lastmod = datetime.fromtimestamp(details.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            file = {
                'name': name,
                'path': path,
                'size': size,
                'last_mod': lastmod
            }
            files.append(file)
        elif os.path.isdir(path):
            folders.append(name)
    return render_template('index.html', back=back, taken=taken, totalgb=totalgb, cdir=cdir, files=files, folders=folders)


@app.route('/uploads/<path:name>')
def download_file(name):
    path = os.path.join(app.config['UPLOAD_FOLDER'], name)
    directory, filename = os.path.split(path)
    if not os.path.isfile(path):
        return redirect(url_for('index'))
    return send_from_directory(directory, filename)


@app.route('/delete/<path:name>')
def delete(name):
    path = os.path.join(app.config['UPLOAD_FOLDER'], name)
    directory, filename = os.path.split(path)
    if os.path.isfile(path):
        os.remove(path)
        cdir = os.path.dirname(name)+'/'
        return redirect(url_for('upload_file', cdir=cdir))
    elif os.path.isdir(path):
        shutil.rmtree(path)
    cdir = os.path.dirname(os.path.dirname(name)) + '/'
    return redirect(url_for('upload_file', cdir=cdir))



if __name__ == '__main__':
    from waitress import serve
    serve(app, host="localhost", port=5000)
