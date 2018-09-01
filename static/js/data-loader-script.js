let siteType = document.getElementById('configType');
let modelName = document.getElementById('modelName');
let numServices = document.getElementById('numServices');
let wrapper = document.getElementById('wrapper');

function displayForm() {
    let backupRouterRow = document.getElementById('backupRouterRow');
    // Declare all backup rows for easy access to hide/display elements
    let backupBandwidthRow = document.getElementById('backupBandwidthRow');
    let primaryManagementHeader = document.getElementById('primaryManagementHeader');
    let backupManagementHeader = document.getElementById('backupManagementHeader');
    let backupManagementRow = document.getElementById('backupManagementRow');
    let terServerRow = document.getElementById('terServerRow');
    let primaryVpnHeader = document.getElementById('primaryVpnHeader');
    let backupVpnHeader = document.getElementById('backupVpnHeader');
    let vpnBodyBackup = document.getElementById('vpnBodyBackup');

    let backupList = [backupBandwidthRow, primaryManagementHeader, backupManagementHeader,
                      backupManagementRow, terServerRow, primaryVpnHeader,
                      backupVpnHeader, vpnBodyBackup];

    if (validateDisplayForm()) {
        if (siteType.value === 'single') {
            for (i=0; i<backupList.length; i++) {
                backupList[i].style.display = "none";
            }
        }
        else if (siteType.value === 'dual') {
            for (i=0; i<backupList.length; i++) {
                backupList[i].style.display = "block";
            }
            vpnBodyBackup.style.display = "block";
        }
        // Lock values to prevent mismatched information from being sent to server (if user changes any values after displaying form)
        numServices.readOnly = true;
        createVpnServices(numServices.value);
        document.getElementsByClassName('form-wrapper')[0].style.display='block';
        wrapper.style.display = 'block';
    }
}

function validateDisplayForm(form) {
    let siteType = document.getElementById('configType');
    let siteTypeError = document.getElementById('siteTypeError');
    let modelName = document.getElementById('modelName');
    let modelNameError = document.getElementById('modelNameError');
    let numServices = document.getElementById('numServices').value;
    let numServicesError = document.getElementById('numServicesError');

    if (siteType.selectedIndex !== 0) {
        siteTypeError.style.display = 'none';
        if (modelName.selectedIndex !== 0) {
            modelNameError.style.display = 'none';
            if (numServices !== '' && numServices !== '0') {
                numServicesError.style.display = 'none';
                return true
            } else { numServicesError.style.display = 'block'; }
        } else { modelNameError.style.display = 'block'; }
    } else { siteTypeError.style.display = 'block'; }
}

function createVpnServices(num) {
    let siteType = document.getElementById('configType').value;
    let vpnBodyPrimary = document.getElementById('vpnBodyPrimary');
    let vpnBodyBackup = document.getElementById('vpnBodyBackup');
    let counter = 1;
    let primaryServiceWrapper = document.getElementById('primaryServiceWrapper');
    let backupServiceWrapper = document.getElementById('backupServiceWrapper');

    //Clear all VPN Service clones if existing
    while (primaryServiceWrapper.firstChild) {
        primaryServiceWrapper.removeChild(primaryServiceWrapper.firstChild);
    }
    while (backupServiceWrapper.firstChild) {
        backupServiceWrapper.removeChild(backupServiceWrapper.firstChild)
    }

    while (counter < num) {
        //Declare lists to store form fields. Field names will be concatenated with the counter variable
        let inputList = [];
        let selectList = [];
        let fieldName;
        counter += 1;
        //Clone VPN Service fields, concatenate 'counter' to their names and append the fields to "vpnServiceWrapper" div
        let clone = vpnBodyPrimary.cloneNode(true);
        clone.id = 'vpnBodyPrimary' + counter;  // Each row is a "vpnBodyPrimary" clone
        inputList = clone.getElementsByTagName('input');
        selectList = clone.getElementsByTagName('select');
        for (i=0; i<inputList.length; i++) {
            fieldName = inputList[i].name;
            clone.getElementsByTagName('input')[i].name = fieldName + counter;
            clone.getElementsByTagName('input')[i].id = fieldName + counter;
        }
        for (i=0; i<selectList.length; i++) {
            fieldName = selectList[i].name;
            clone.getElementsByTagName('select')[i].name = fieldName + counter;
            clone.getElementsByTagName('select')[i].id = fieldName + counter;
        }
        primaryServiceWrapper.appendChild(clone);

        if (siteType === 'dual') {
            let clone = vpnBodyBackup.cloneNode(true);
            clone.id = 'vpnBodyBackup' + counter;
            inputList = clone.getElementsByTagName('input');
            selectList = clone.getElementsByTagName('select');
            for (i=0; i<inputList.length; i++) {
                fieldName = inputList[i].name;
                clone.getElementsByTagName('input')[i].name = fieldName + counter;
                clone.getElementsByTagName('input')[i].id = fieldName + counter;
            }
            for (i=0; i<selectList.length; i++) {
                fieldName = selectList[i].name;
                clone.getElementsByTagName('select')[i].name = fieldName + counter;
                clone.getElementsByTagName('select')[i].id = fieldName + counter;
            }
            backupServiceWrapper.appendChild(clone)
        }
    }
}

function validateIP(ipAddress){
    ipv4Re = new RegExp(/^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$|^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$/);
    if(ipv4Re.test(ipAddress)) {
        return true
    } else return false
}

function submitForm(){
    document.getElementById('input_form').submit();
}

function resetForm(){
    let numServices = document.getElementById('numServices');
    let answer = confirm('Reset fields?')
    if (answer) {
        location = location.href
    }
}

// Filling in NMS VLAN will increment HOT Facility VLAN by 1
function incrementManagementVlan(nmsField, facilityField){
    let nms = document.getElementById(nmsField);
    let facility = document.getElementById(facilityField);
    facility.value = Number(nms.value) + 1
}

// Filling in the first row of a service's VLAN will populate the other's with an incremented value
function incrementServiceVlan(field, num){
    let value = Number(document.getElementById(field).value);
    let vlan;
    // i=2 (Start at serviceVlan2) while number of services + 1 (because we skipped first serviceVlan) is less than i
    for (i=2; i<Number(num)+1; i++){
        let fieldName = field + i
        value = value + 1
        document.getElementById(fieldName).value = value;
    }
}

function toggleValidateIP(){
    if (validateIP(this.value)){
        this.setAttribute('style', 'background-color: white')
    } else {
        this.setAttribute('style', 'background-color: #ffcccc')
    }
}


document.getElementById('showForm').addEventListener('click', displayForm);
document.getElementById('cpeLoopback').addEventListener('change', toggleValidateIP);
document.getElementById('nmsIP').addEventListener('change', toggleValidateIP);
document.getElementById('facilityIP').addEventListener('change', toggleValidateIP);
document.getElementById('servicePeIP').addEventListener('change', toggleValidateIP);
document.getElementById('nmsVlan').addEventListener('change', function(){ incrementManagementVlan('nmsVlan', 'facilityVlan') });
document.getElementById('nmsVlanBackup').addEventListener('change', function(){ incrementManagementVlan('nmsVlanBackup', 'facilityVlanBackup') });
document.getElementById('serviceVlan').addEventListener('change', function(){ incrementServiceVlan('serviceVlan', numServices.value) });
document.getElementById('serviceVlanBackup').addEventListener('change', function(){ incrementServiceVlan('serviceVlanBackup', numServices.value) });
document.getElementById('resetButton').addEventListener('click', resetForm);

