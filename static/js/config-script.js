if (document.getElementById('numServicesHidden')) {
    var numServices = document.getElementById('numServicesHidden').value;
    var siteType = document.getElementById('siteTypeHidden').value;
    var siteSuffix = [''];
    if (siteType === 'dual') {
        siteSuffix.push('Backup');
    }
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

function displayForm() {
    let wrapper = document.getElementById('wrapper');

    createVpnServices(numServices);
}

function togglePeRouter() {
    if (this.value === 'dual') {
        document.getElementById('peRouterBackup').classList.remove('hidden')
    } else {
        document.getElementById('peRouterBackup').classList.add('hidden')
    }
}

function submitForm() {
    let button = document.getElementById('submitButton');
    let errors = document.getElementById('errorList');
    let missing = [];
    if (!form.checkValidity()) {
        const temp = document.createElement('button')
        form.appendChild(temp)
        temp.click()
        form.removeChild(temp)

        // Clear previous error list
        while (errors.firstChild) {
            errors.removeChild(errors.firstChild);
        }
        let fields = document.querySelectorAll('[required]')
        for (i=0; i<fields.length; i++) {
            if (fields[i].value === ''){
                missing.push(fields[i].id);
            }
        }

        // Append each error to a bullet point
        for (i=0; i<missing.length; i++) {
            let bullet = document.createElement('li');
            let text = document.createTextNode(missing[i]);
            bullet.appendChild(text);
            errors.appendChild(bullet);
        }
        document.getElementById('errorAlert').classList.remove('hidden');
    } else {
        form.submit();
    }
}


function validateNumServices(num){
    let numServicesError = document.getElementById('numServicesError');

    if (isNaN(num) || num === "") {
        numServicesError.innerHTML = 'Invalid number'
        numServicesError.style.display = 'block';
        return false;
    } else if (num > 8) {
        numServicesError.innerHTML = "That's a lot of services"
        numServicesError.style.display = 'block';
        return false;
    } else {
        numServicesError.style.display = 'none';
        return true;
    }
}

function createVpnServices(num) {
    for (x=0; x<siteSuffix.length; x++) {
        let serviceBody = document.getElementById('serviceBody' + siteSuffix[x]);
        let counter = 1;
        let vpnWrapper = document.getElementById("vpnServiceWrapper" + siteSuffix[x]);
        while (counter < num) {
            //Declare lists to store form fields. Field names will be concatenated with the counter variable
            let fieldList = [];
            let fieldName;
            let collapse = 'vpnServiceCollapse' + siteSuffix[x];
            counter += 1;
            //Clone VPN Service fields, concatenate 'counter' to their names and append the fields to "vpnServiceWrapper" div
            let clone = serviceBody.cloneNode(true);
            clone.id = 'serviceBody' + siteSuffix[x] + counter;
            fieldList = clone.querySelectorAll('.form-control');
            labelList = clone.querySelectorAll('label');
            divList = clone.getElementsByTagName('div');

            clone.getElementsByTagName('span')[0].innerHTML = counter;
            for (i=0; i<fieldList.length; i++) {
                fieldName = fieldList[i].name;
                fieldList[i].name = fieldName + counter;
                fieldList[i].id = fieldName + counter;
                // Increment labels
                for (j=0; j<labelList.length; j++) {
                    if (labelList[j].getAttribute('for') == fieldName) {
                        labelList[j].setAttribute('for', fieldName + counter)
                    }
                }
                if (divList[i].id === collapse) {
                    divList[i].id = collapse + counter;
                }
            }

            // Collapse all clones and change their icons
            for (i=0; i<divList.length; i++) {
                if (divList[i].id.includes('vpnServiceCollapse')) {
                    divList[i].classList.remove('show');
                    divList[i].classList.add('collapse');
                    let icon = clone.getElementsByClassName('icon')[0];
                    let label = clone.querySelectorAll('a')[0]
                    icon.classList.add('fa-plus');
                    icon.classList.remove('fa-minus')
                    label.classList.add('collapsed')
                }
            }

            // Clone accordion elements
            header = clone.getElementsByTagName('a')[0];
            header.href = '#' + collapse + counter;

            vpnWrapper.appendChild(clone);
        }
    }
}

function routeSplash(){
    window.location = this.value
}

function routePeRouter(){
    validateNumServices(document.getElementById('numServices').value);

    if (validateNumServices(document.getElementById('numServices').value)) { return true; }
    else { return false; }
}

function validateIP(ipAddress){
    ipv4Re = new RegExp(/^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$|^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$/);
    if(ipv4Re.test(ipAddress)) {
        return true
    } else return false
}

function toggleValidateIP(){
    if (validateIP(this.value)){
        this.setAttribute('style', 'background-color: white')
        // Assuming all PE IP's are /30, subtract 1 from last octet of IP if the octet isn't divisible by 2
        if (this.name.includes('servicePeIP') || this.name.includes('serviceCpeIP')) {
            toNetworkIP(this)
        }
    } else {
        this.setAttribute('style', 'background-color: #ffcccc')
    }
}

// If an IP addresses last octet is an uneven number, decrement it by 1. This assumes the first available IP is input.
function toNetworkIP(ip) {
    let octets = ip.value.split('.')
    if (octets.length === 4) {
        let lastOctet = parseInt(octets[3]);
        if (lastOctet % 2 !== 0) {
            lastOctet -= 1
            octets.splice(3);
            octets.push(lastOctet);
            ip.value = octets.join('.')
        }
    }
}

function incrementManagementVlans(){
    if (this.name.includes('Backup')) {
        document.getElementById('vpnConcVlanBackup').value = parseInt(this.value) + 1
    } else {
        document.getElementById('vpnConcVlan').value = parseInt(this.value) + 1
    }

}

function incrementIPSLA() {
    let primaryIPSLA = this.value;  // Get value of primary IP SLA field
    let firstDigit = parseInt(primaryIPSLA.slice(0,1)) + 1;  // Extract first digit from primary IP SLA and increase by 1
    let subtractFirst =  primaryIPSLA.slice(1);  // Remove first digit from primary IP SLA
    let backupIPSLA = "" + firstDigit + subtractFirst;  // Replace removed first digit with incremented value
    let name = this.attributes['name'].value;
    let suffix = name.slice(-1);
    let fieldName;

    if (this.name.includes('Backup')) {
        fieldName = 'serviceIPSLABackupBackup';
    } else {
        fieldName = 'serviceIPSLABackup';
    }
    if (isNaN(suffix)) {
        document.getElementById(fieldName).value = backupIPSLA
    } else {
        document.getElementById(fieldName + suffix).value = backupIPSLA
    }
}

// Toggles plus & minus sign to display form sections
function toggleHeaderIcon() {
    let icon = this.getElementsByClassName('icon')[0];
    if (this.classList.contains('collapsed')) {
        icon.classList.add('fa-minus');
        icon.classList.remove('fa-plus')
    } else {
        icon.classList.add('fa-plus');
        icon.classList.remove('fa-minus')
    }
}


function incrementServiceVlans() {
    for (x=0; x<siteSuffix.length; x++) {
        let vlan = parseInt(this.value);
        let fieldName = 'serviceVlan' + siteSuffix[x];
        let suffix = 2;

        // Subtract 1 from num because first VLAN doesn't need its value changed
        for (i=0; i<numServices-1; i++) {
            vlan += 1;
            document.getElementById(fieldName + suffix).value = vlan;  // Loop starts at serviceVlan2
            suffix += 1
        }
    }
}

function fillServiceBandwidth() {
    for (x=0; x<siteSuffix.length; x++) {
        let bw = parseInt(document.getElementById('siteBandwidth' + siteSuffix[x]).value) - 1;
        console.log('siteBandwidth'+siteSuffix[x]);
        let fieldName = 'serviceBandwidth' + siteSuffix[x];
        let suffix = 1;

        for (i=0; i<numServices; i++) {
            if (suffix === 1) { document.getElementById(fieldName).value = bw; }
            else { document.getElementById(fieldName + suffix).value = bw; }
            suffix += 1
        }
    }
}


function fillBackupServiceType() {
    let suffix = this.name.slice(this.name.length - 1)
    if (isNaN(suffix)) {
        suffix = ''
    }
    document.getElementById('serviceTypeBackup' + suffix).value = this.value;
}

if (document.getElementById('numServicesHidden')) {
    document.addEventListener('DOMContentLoaded', displayForm);
    document.getElementById('submitButton').addEventListener('click', submitForm);
    document.getElementById('loopbackIP').addEventListener('change', toggleValidateIP);
    document.getElementById('msuID').addEventListener('change', function(){
        last = this.value.split('')[this.value.length - 1].toUpperCase();
        if (last === 'A') {
            document.getElementById('msuIDBackup').value = this.value.slice(0, this.value.length-1) + 'B';
        }
    })

    for (x=0; x<siteSuffix.length; x++) {
        document.getElementById('nmsIP' + siteSuffix[x]).addEventListener('change', toggleValidateIP);
        document.getElementById('vpnConcIP' + siteSuffix[x]).addEventListener('change', toggleValidateIP);
        document.getElementById('serviceVlan' + siteSuffix[x]).addEventListener('keyup', incrementServiceVlans);
        document.getElementById('siteBandwidth' + siteSuffix[x]).addEventListener('keyup', fillServiceBandwidth);
        document.getElementById('nmsVlan' + siteSuffix[x]).addEventListener('keyup', incrementManagementVlans);
    }
}

if (document.getElementById("configType")) {
    document.getElementById("configType").addEventListener('change', routeSplash);
}
if (document.getElementById("siteType")){
    // Toggle backup PE router
    document.getElementById("siteType").addEventListener('change', function(){
        if (this.value === 'dual') {
            document.getElementById('peBackup').classList.remove('hidden')
            document.getElementById('peBackup').required = true;
        } else {
            document.getElementById('peBackup').classList.add('hidden')
            document.getElementById('peBackup').required = false;
        }
    })
}

if (document.getElementById('configTextArea')) {
    document.getElementById('cpeToggle').addEventListener('click', toggleHeaderIcon);
    document.getElementById('switchToggle').addEventListener('click', toggleHeaderIcon);
    document.getElementById('vpnToggle').addEventListener('click', toggleHeaderIcon);
    document.getElementById('peToggle').addEventListener('click', toggleHeaderIcon);
    document.getElementById('ipslaToggle').addEventListener('click', toggleHeaderIcon);

    document.getElementById('cpeToggleBackup').addEventListener('click', toggleHeaderIcon);
    document.getElementById('switchToggleBackup').addEventListener('click', toggleHeaderIcon);
    document.getElementById('vpnToggleBackup').addEventListener('click', toggleHeaderIcon);
    document.getElementById('peToggleBackup').addEventListener('click', toggleHeaderIcon);
    document.getElementById('ipslaToggleBackup').addEventListener('click', toggleHeaderIcon);
}

if (document.getElementById('configDownload')) {
    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('siteTypeHidden').value === 'dual') {
            document.getElementById('configTextAreaBackup').style.display = 'block';
        } else {
            document.getElementById('configTextAreaBackup').style.display = 'none';
        }
    })
}

$(function () {
    $("select.portSelect").change(function () {
        $("select.portSelect option[value='" + $(this).data('index') + "']").prop('disabled', false); // reset others on change everytime
        $(this).data('index', this.value);
        $("select.portSelect option[value='" + this.value + "']:not([value=''])").prop('disabled', true);
        $(this).find("option[value='" + this.value + "']:not([value=''])").prop('disabled', false); // Do not apply the logic to the current one
    });
});



