from flask import abort
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from openpyxl import load_workbook
from pathlib import Path
from config_generator import strip_whitespace
import ipaddress
from zipfile import ZipFile

# Folders and file names
DATABASE = 'sqlite:///database/dataloader_db.sqlite?check_same_thread=False'
DATA_FOLDER = Path('served_files/dataloader')
TEMPLATE_FILE = str(DATA_FOLDER / 'Template.xlsx')
R3_DATA_FILE = str(DATA_FOLDER / 'Region 3 Data File.xlsx')
R1_DATA_FILE = str(DATA_FOLDER / 'Region 1 Data File.xlsx')

# Initial configuration of SQLAlchemy engine and connection
Base = automap_base()
engine = create_engine(DATABASE)
Base.prepare(engine, reflect=True)

# Map tables from database
Equipment = Base.classes.equipment_templates
Srx345Ports = Base.classes.srx345_physical_ports
Asr9k = Base.classes.asr9k_routers
PeSite = Base.classes.pe_sites
FacilityVpnPorts = Base.classes.hf_vpn_ports
ServiceVpnPorts = Base.classes.service_vpn_ports
NmsPePorts = Base.classes.nms_pe_ports
ServicePePorts = Base.classes.service_pe_ports
SubnetMasks = Base.classes.subnet_masks

session = Session(engine)


class Port:
    pass

class Shelf:
    def __init__(self, shelf_id, site_id=None, shelf_template=None, ip_addr=None):
        self.shelf_id = shelf_id
        if site_id is None:
            q = session.query(PeSite).filter(PeSite.shelf_clei == shelf_id).first()
            self.site_id = q.pop_clli
        else:
            self.site_id = site_id
        self.shelf_template = shelf_template
        self.ip_addr = ip_addr
        

class Subnet:
    pass

class Channel:
    pass



def create_r3_data_file(form):
    # Load template and assign sheets to variables
    wb = load_workbook(TEMPLATE_FILE)
    SHELF_SHEET = wb['SHELF']
    PORT_SHEET = wb['PORT']
    SUBNET_SHEET = wb['SUBNET']
    IP_SHEET = wb['IP']
    CHANNEL_SHEET = wb['CHANNEL']

    shelf_rows = {}
    port_rows = {}
    subnet_rows = []
    channel_rows = []
    
    d = strip_whitespace(form)
    
    shelf_rows.update({'a': Shelf(d['peRouter1'])})
    
    
    
    row_counter = 2
    for key, value in shelf_rows.items():
        SHELF_SHEET['A{}'.format(row_counter)] = value.shelf_id
        SHELF_SHEET['B{}'.format(row_counter)] = value.site_id
        SHELF_SHEET['C{}'.format(row_counter)] = value.shelf_template
        row_counter += 1
        
    wb.save('ADSASD.xlsx')



if __name__ == '__main__':
    form = {
        'peRouter1': 'OTWBONPZPED10',
        'siteBandwidth': '100',
        'facilityVlan': '640',
        'nmsVlan': '639',
        'vendorInterface': 'GIG',
        'vendorPort': '0/1/0/18',
        'vendorChannel': '0001-10GIG-E-OTWBONPZPED01-OTWBONPZD00-ROGERS',
        'vendorVlan': '600-601',
        'siteBandwidthBackup': '50',
        'peRouter2': 'TOROONXNPED10',
        'siteType': 'dual',
        'facilityVlanBackup': '990',
        'nmsVlanBackup': '989',
        'vendorInterfaceBackup': 'TEN',
        'vendorPortBackup': '0/1/0/69',
        'vendorChannelBackup': '0005-10GIG-E-OTWBONPZPED01-OTWBONPZD00-ROGERS',
        'vendorVlanBackup': '1000-1001',
    }
    
    create_r3_data_file(form)

    
    pass