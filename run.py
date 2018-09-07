from flask import Flask, render_template, request, send_file, url_for, redirect
from pathlib import Path
import dataloader as dl
from datetime import date
import config_generator as cg
import time
import os

# Global Variables
DATABASE = 'database/database.sqlite'
DATA_FOLDER = Path('served_files/dataloader')
DATA_ZIP_FILE = 'Data Files.zip'
DATA_ZIP_SERVED = ''
DATA_R1_FILE = 'Region 1 Data File.xlsx'
DATA_R3_FILE = 'Region 3 Data File.xlsx'
CONFIG_FOLDER = Path('served_files/config_generator/')
CONFIG_FILE = ''

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def home():
    tools = ['config_generator.py', 'dataloader.py']
    tools_modified = {}
    for tool in tools:
        tools_modified.update({tool: time.strftime("%m/%d/%Y",time.localtime(os.path.getmtime(tool)))})
    return render_template('index.html', tools_modified=tools_modified)

@app.route('/ehealth')
def ehealth():
    return render_template('ehealth.html')


@app.route('/coin')
def coin():
    return render_template('coin.html')


@app.route('/test')
def test():
    return render_template('config_generator/config-generator-success-tabs.html')


@app.route('/config-generator')
def config_generator():
    return render_template('config_generator/config-generator-splash.html')


@app.route('/config-generator/<equipment>', methods=['GET', 'POST'])
def equipment_template(equipment):
    dropdown_lists = cg.dropdown_lists()
    if equipment == 'srx':
        if request.method == 'GET':
            return render_template('config_generator/srx-config-select.html',
                                   dropdown_lists=dropdown_lists
                                   )
        elif request.method == 'POST':
            form = request.form.to_dict()
            if form['siteType'] == 'dual':
                return redirect(url_for(
                    'new_srx_config', 
                    srx=form['srxDevice'].lower(),
                    site=form['siteType'].lower(), 
                    router=form['peRouter'].lower(),
                    b_router=form['peRouterBackup'].lower(),
                    services=form['numServices'],
                ))
            else:
                return redirect(url_for(
                    'new_srx_config', 
                    srx=form['srxDevice'].lower(),
                    site=form['siteType'].lower(), 
                    router=form['peRouter'].lower(),
                    services=form['numServices'],
                ))
    elif equipment == 'asr':
        return render_template('config_generator/asr-config.html')


@app.route('/config-generator/<srx>/<site>/<router>/<services>', defaults={'b_router': None}, methods=['GET', 'POST'])
@app.route('/config-generator/<srx>/<site>/<router>/<b_router>/<services>', methods=['GET', 'POST'])
def new_srx_config(srx, site, router, services, b_router):
    dropdown_lists = cg.dropdown_lists(srx)

    if request.method == 'GET':
        srx_page = 'config_generator/{site}-{srx}.html'.format(site=site, srx=srx)
        return render_template(
            srx_page,
            site=site,
            services=services,
            device=srx,
            dropdown_lists=dropdown_lists
        )
    elif request.method == 'POST':
        text_configs = cg.generate_configs(request.form.to_dict(), router, b_router)

        # Add site ID to zip folder
        global CONFIG_FILE
        CONFIG_FILE = text_configs['config_zip']
        return render_template('config_generator/config-generator-success.html', site=site, text_configs=text_configs)


@app.route('/data-loader', methods=['GET', 'POST'])
def data_loader():
    dropdown_lists = dl.dropdown_lists()

    if request.method == 'GET':
        return render_template('/dataloader/data-loader.html', dropdown_lists=dropdown_lists)
    elif request.method == 'POST':
        form = request.form.to_dict()
        dl.zip_data_files(form)
        global DATA_ZIP_SERVED
        DATA_ZIP_SERVED = '{site} Data Files - {date}.zip'.format(site=form['siteCLLI'], date=str(date.today()))
        return render_template('/dataloader/data-loader-success.html')


@app.route('/download-file/<file_type>')
def download_file(file_type):
    file = ''  # File will change depending on file_type parameter
    file_name = ''
    if file_type == 'data_zip':
        file = str(DATA_FOLDER / DATA_ZIP_FILE)
        file_name = DATA_ZIP_SERVED
    elif file_type == 'data_r3':
        file = str(DATA_FOLDER / DATA_R3_FILE)
        file_name = DATA_R3_FILE
    elif file_type == 'data_r1':
        file = str(DATA_FOLDER / DATA_R1_FILE)
        file_name = DATA_R1_FILE
    elif file_type == 'config_zip':
        file = str(CONFIG_FOLDER / CONFIG_FILE)
        file_name = CONFIG_FILE

    return send_file(file, attachment_filename=file_name, as_attachment=True)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html', error=str(e)), 404


@app.errorhandler(400)
def internal_server_error(error):
    return render_template('error/400.html', error=error.description), 400

    
if __name__ == '__main__':
    app.run(use_reloader=True)
