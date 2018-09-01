let PE_ROUTERS = {
  EBCKONCBPED10 : {
    srx : 'EBCKONCB45W',
    site : 'EBCKONCBM00',
    asr9k: 'EBCKONCBPED01'
  },

  EBCKONCBPED11 : {
    srx:'EBCKONCB45W',
    site:'EBCKONCBM00',
    asr9k: 'EBCKONCBPED01'
  },

  HMTNONKJPED10 : {
    srx: 'HMTNONKJ45W',
    site: 'HMTNONKJD00',
    asr9k: 'HMTNONKJPED01'
  },

  KGTNONGWPED10 : {
    srx: 'KGTNONGW45W',
    site: 'KGTNONGWD00',
    asr9k: 'KGTNONGWPED01'
  },

  KTNRONOMPED10 : {
    srx: 'KTNRONOM45W',
    site: 'KTNRONOMD00',
    asr9k: 'KTNRONOMPED01'
  },

  LONDONATPED10 : {
    srx: 'LONDONAT45W',
    site: 'LONDONATD02',
    asr9k: 'LONDONATPED01'
  },

  OTWBONPZPED10 : {
    srx: 'OTWBONPZ45W',
    site: 'OTWBONPZD00',
    asr9k: 'OTWBONPZPED01'
  },

  SDBRONEMPED10 : {
    srx: 'SDBRONEM45W',
    site: 'SDBRONEMD00',
    asr9k: ''
  },

  TDBAONIZPED10 : {
    srx: 'TDBAONIZ45W',
    site: 'TDBAONIZD00',
    asr9k: ''
  },

  TOROONXNPED10 : {
    srx: 'TOROONXN45W',
    site: 'TOROONXND15',
    asr9k: 'TOROONXNPED01'
  },

  TOROONXNPED11 : {
    srx: 'TOROONXN45W',
    site: 'TOROONXND15',
    asr9k: 'TOROONXNPED01'
  },

  UTOPONADPED10 : {
    srx: 'UTOPONAD45W',
    site: 'UTOPONADD00',
    asr9k: 'UTOPONADPED01'
  },

  WNDSONWGPED10 : {
    srx : 'WNDSONWG45W',
    site: 'WNDSONWGD00',
    asr9k: 'WNDSONWGPED01'
  }
};

let ASR9K_ROUTERS = {
  EBCKONCBPED01 : {site: 'EBCKONCBM00'},
  HMTNONKJPED01 : {site: 'HMTNONKJD00'},
  KGTNONGWPED01 : {site: 'KGTNONGWD00'},
  KTNRONOMPED01 : {site: 'KTNRONOMD00'},
  LONDONATPED01 : {site: 'LONDONATD02'},
  OTWBONPZPED01 : {site: 'OTWBONPZD00'},
  TOROONXNPED01 : {site: 'TOROONXND27'},
  UTOPONADPED01 : {site: 'UTOPONADD00'},
  WNDSONWGPED01 : {site: 'WNDSONWGD00'}
};

let siteBWPrimary = document.getElementById("siteBW");
let peRouterPrimary = document.getElementById("peRouterList");
let cpeRouterPrimary = document.getElementById("cpeRouter");
let srx3600Primary = document.getElementById("srx3600");
let asr9kPrimary = document.getElementById("asr9k");
let aSitePrimary = document.getElementById("aSite");
let zSitePrimary = document.getElementById("zSite");
let primaryFields = [siteBWPrimary, cpeRouterPrimary, zSitePrimary];

let siteBWRedundant = document.getElementById("siteBWRe");
let peRouterRedundant = document.getElementById("peRouterListRe");
let cpeRouterRedundant = document.getElementById("cpeRouterRe");
let srx3600Redundant = document.getElementById("srx3600Re");
let asr9kRedundant = document.getElementById("asr9kRe");
let aSiteRedundant = document.getElementById("aSiteRe");
let zSiteRedundant = document.getElementById("zSiteRe");
let redundantFields = [siteBWRedundant, cpeRouterRedundant, zSiteRedundant];

let singleCpeFields = document.getElementById("singleCpeFields");
let dualCpeFields = document.getElementById("dualCpeFields");

let nmsTag = "NMS-";

/* Hide/display single CPE and dual CPE fields */
function showForm(site) {
  let siteType = site;

  if (siteType === 'primary') {
    nmsTag = "NMS-";
    singleCpeFields.style.display = "block";
    dualCpeFields.style.display = "none";
    document.getElementById("pSiteLabel").innerHTML = "Site Fields";
    document.getElementById("pPathLabel").innerHTML = "Path Names";
  }
  else if (siteType === 'redundant'){
    nmsTag = "NMS-01";
    singleCpeFields.style.display = "block";
    dualCpeFields.style.display = "block";
    document.getElementById("pSiteLabel").innerHTML = "Primary Site Fields";
    document.getElementById("pPathLabel").innerHTML = "Primary Path Names";
    document.getElementById("divider").style.display = "block";
  }
}

function generatePaths(site) {
  let siteType = site;

  if (siteType === 'primary') {
    let bwMinus = siteBWPrimary.value - 1;
    if (document.getElementById("dualCpeOption").checked){
      nmsTag = "NMS-01-";
    }
    let r3al = "0001-" + siteBWPrimary.value + "M-" + aSitePrimary.value + "-" + cpeRouterPrimary.value;
    let r3hf = "0001-" + bwMinus + "M-" + srx3600Primary.value + "-" + cpeRouterPrimary.value;
    let r3nms = nmsTag + cpeRouterPrimary.value;
    let peSrx = "GIG-RE-" + peRouterPrimary.value + "-" + srx3600Primary.value;
    let r1al = "0001-" + siteBWPrimary.value + "M-" + asr9kPrimary.value + "-" + zSitePrimary.value;
    let r1hf = "REGION3-" + r3hf;
    let r1nms = "REGION3-" + nmsTag + zSitePrimary.value;

    document.getElementById("r3AccessLink").value = r3al;
    document.getElementById("r3HotFacility").value = r3hf;
    document.getElementById("r3Nms").value = r3nms;
    document.getElementById("peToSrx").value = peSrx;
    document.getElementById("r1AccessLink").value = r1al;
    document.getElementById("r1HotFacility").value = r1hf;
    document.getElementById("r1Nms").value = r1nms;

    if (siteBWPrimary.readOnly === false) {
      toggleLock('primary');
    }
  }

  else if (siteType === 'redundant') {
    let bwMinus = siteBWRedundant.value - 1 ;
    let r3alRe = "0002-" + siteBWRedundant.value + "M-" + aSiteRedundant.value + "-" + cpeRouterRedundant.value;
    let r3hfRe = "0002-" + bwMinus + "M-" + srx3600Redundant.value + "-" + cpeRouterRedundant.value;
    let r3nmsRe = "NMS-02-" + cpeRouterRedundant.value;
    let peSrxRe = "GIG-RE-" + peRouterRedundant.value + "-" + srx3600Redundant.value;
    let r1alRe = "0002-" + siteBWRedundant.value + "M-" + asr9kRedundant.value + "-" + zSitePrimary.value;
    let r1hfRe = "REGION3-" + r3hfRe;
    let r1nmsRe = "REGION3-NMS-02-" + zSitePrimary.value;

    document.getElementById("r3AccessLinkRe").value = r3alRe;
    document.getElementById("r3HotFacilityRe").value = r3hfRe;
    document.getElementById("r3NmsRe").value = r3nmsRe;
    document.getElementById("peToSrxRe").value = peSrxRe;
    document.getElementById("r1AccessLinkRe").value = r1alRe;
    document.getElementById("r1HotFacilityRe").value = r1hfRe;
    document.getElementById("r1NmsRe").value = r1nmsRe;

    if (siteBWRedundant.readOnly === false) {
      toggleLock('redundant');
    }
  }
}

function toggleLock(site) {
  let siteType = site;

  if (siteType === 'primary') {
    if (siteBWPrimary.readOnly) {
      for(x=0; x < primaryFields.length; x++) {
        primaryFields[x].readOnly = false;
      }
      peRouterPrimary.disabled = false;
      document.getElementById("lockIcon").setAttribute("class","fas fa-lock")
    }
    else {
      for(x=0; x < primaryFields.length; x++) {
        primaryFields[x].readOnly = true;
      }
      peRouterPrimary.disabled = true;
      document.getElementById("lockIcon").setAttribute("class","fas fa-lock-open");
    }
  }

  else if (siteType === 'redundant') {
    if (siteBWRedundant.readOnly) {
      for(x=0; x < redundantFields.length; x++) {
        redundantFields[x].readOnly = false;
      }
      peRouterRedundant.disabled = false;
      document.getElementById("lockIconRe").setAttribute("class","fas fa-lock")
    }
    else {
      for(x=0; x < redundantFields.length; x++) {
        redundantFields[x].readOnly = true;
      }
      peRouterRedundant.disabled = true;
      document.getElementById("lockIconRe").setAttribute("class","fas fa-lock-open");
    }
  }
}

function resetFields(site) {
  let siteType = site;

  if (siteType === 'primary') {
    if (siteBWPrimary.readOnly = true) {
      toggleLock(siteType);
    }
  }
  else if (siteType === 'redundant') {
    if (siteBWRedundant.readOnly = true) {
      toggleLock(siteType);
    }
  }
}

function fillPeRouterFields(site) {
  let siteType = site;
  let peRouterDropdown;
  let peRouter;
  let asr9k;

  if (siteType === 'primary') {
    peRouterDropdown = document.getElementById('peRouterList');
    peRouter = peRouterDropdown.value;
    asr9k = PE_ROUTERS[peRouter].asr9k;
    srx3600Primary.value = PE_ROUTERS[peRouter].srx;
    asr9kPrimary.value = asr9k;
    aSitePrimary.value = ASR9K_ROUTERS[asr9k].site;
  }
  else if (siteType === 'redundant') {
    peRouterDropdown = document.getElementById('peRouterListRe');
    peRouter = peRouterDropdown.value;
    asr9k = PE_ROUTERS[peRouter].asr9k;
    srx3600Redundant.value = PE_ROUTERS[peRouter].srx;
    asr9kRedundant.value = asr9k;
    aSiteRedundant.value = ASR9K_ROUTERS[asr9k].site;
  }
}

function autofillDualCpe() {
  cpeRouterRedundant.value = cpeRouterPrimary.value;
  zSiteRedundant.value = zSitePrimary.value;
}


/*-----------------------Event Listeners-----------------------*/

//Single CPE
document.getElementById('singleCpeOption').addEventListener('click', function() { showForm('primary') });
document.getElementById('peRouterList').addEventListener('change', function() { fillPeRouterFields('primary') });
document.getElementById('cpeRouter').addEventListener('blur', autofillDualCpe);
document.getElementById('zSite').addEventListener('blur', autofillDualCpe);
document.getElementById('genPathsBtnPrimary').addEventListener('click', function() { generatePaths('primary') });
document.getElementById('toggleLockBtnPrimary').addEventListener('click', function() { toggleLock('primary') });
document.getElementById('resetBtnPrimary').addEventListener('click', function() { resetFields('primary') });

//Dual CPE
document.getElementById('dualCpeOption').addEventListener('click', function() { showForm('redundant') });
document.getElementById('peRouterListRe').addEventListener('change', function() { fillPeRouterFields('redundant') });
document.getElementById('genPathsBtnRedundant').addEventListener('click', function() { generatePaths('redundant') });
document.getElementById('toggleLockBtnRedundant').addEventListener('click', function() { toggleLock('redundant') });
document.getElementById('resetBtnRedundant').addEventListener('click', function() { resetFields('redundant') });



