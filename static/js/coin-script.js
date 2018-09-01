let popCodeList = {
    'ALX':'ALXNONASWDM01',
    'APL':'APHLONACWDM01',
    'BBR':'BMTNONGNWDM01',
    'BBT':'BURLONRHWDM01',
    'BED':'BDLLONAAWDM01',
    'BHA':'HMTNONKJWDM01',
    'BMY':'BMMLON01WDM01',
    'BOM':'BWMVONBZWDM01',
    'BOT':'BOTNONBEWDM01',
    'BPX':'PTBOONQFWDM01',
    'BT2':'BITNONAYWDM01',
    'BTN':'BITNONAWWDM01',
    'CGI1':'MSSGONAPWDM01',
    'CGI2':'MSSGONAPWDM02',
    'CLE':'MRHMONBRWDM01',
    'CTM':'CHHMONGKWDM01',
    'CTQ':'CTRQONAAWDM01',
    'CWD':'PCNGONGCWDM01',
    'EDW':'STTMONEAWDM01',
    'ESA':'UTOPONADWDM01',
    'FGW':'FRGSONBBWDM01',
    'GBY':'GRMSONBKWDM01',
    'GST':'BMTNONHTWDM01',
    'H24':'HMTNONWCWDM01',
    'IBM3':'UNVLONSAWDM01',
    'IDC':'BARION79WDM01',
    'KIT':'KTNRONOMWDM01',
    'LET':'KGTNONMAWDM01',
    'LON':'LONDONATWDM01',
    'LSY':'LNDSONBKWDM01',
    'MDP':'CLDNONATWDM01',
    'MLT':'MLTNONFAWDM01',
    'MRL':'MTLXPQAKWDM01',
    'MTL7':'MTLXPQAKWDM01',
    'ORL': 'ORLLONEHWDM01',
    'OS2':'OSHWONFPWDM01',
    'OTA':'OTWBONPZWDM01',
    'OTT':'OTWBONJJWDM01',
    'PLM1':'TORYONRRWDM01',
    'PLM2':'TORYONRRWDM02',
    'RCH':'EBCKONCBWDM01',
    'SFD':'SRFRONDTWDM01',
    'SGD1':'MSSMONPWWDM01',
    'SGD2':'MSSMONPWWDM02',
    'SMF':'SMFLONCBWDM01',
    'SMY':'STMYONBUWDM01',
    'SVS1':'SSVLONAAWDM01',
    'SVS2':'SSVLONAAWDM02',
    'TCH':'TORTONAFWDM01',
    'TFS':'TOROONXNWDM01',
    'WLM':'BARIONUOWDM01',
    'WPK':'BMTNONWRWDM01',
    'WSR':'WNDSONWGWDM01',
    'YRG':'GLPHONATWDM01',
    'ALB':'TRLDONBNWDM01' };

$("#myModal").modal();

function generateCoinPath() {
    let generatedCoinPath = document.getElementById('generatedCoinPath');
    let pop1Input = document.getElementById('pop1Input').value.toUpperCase();
    let pop2Input = document.getElementById('pop2Input').value.toUpperCase();
    let pop1 = popCodeList[pop1Input];
    let pop2 = popCodeList[pop2Input];

    if (pop1 < pop2) {
        generatedCoinPath.value = "OPTICAL-" + pop1 + "-" + pop2;
    }
    else {
        generatedCoinPath.value = "OPTICAL-" + pop2 + "-" + pop1;
    }
}

function resetCoin(){
    document.getElementById("pop1Message").style.visibility = "hidden";
    document.getElementById("pop2Message").style.visibility = "hidden";
}

function validatePopCode(pop, numPop) {
    let coinMessage = document.getElementById(numPop + "Message");
    let coinMessageContent;

    let popCode = document.getElementById(pop).value.toUpperCase();

    if (popCodeList[popCode]) {
        coinMessageContent = popCodeList[popCode];
        coinMessage.innerHTML = coinMessageContent;
        coinMessage.style.visibility = "visible";
        coinMessage.style.color = "black";
        return popCodeList[popCode];
    } else {
        coinMessageContent = "Invalid POP Code";
        coinMessage.innerHTML = coinMessageContent;
        coinMessage.style.visibility = "visible";
        coinMessage.style.color = "red";
    }
}

function generateDwdmTable(){
    let table = document.getElementById('coinTableBody');
    let tr, pop, dwdm;

    for (let key in popCodeList) {
        popText = document.createTextNode(key);
        dwdmText = document.createTextNode(popCodeList[key]);
        tr = document.createElement("tr");
        pop = document.createElement("td");
        dwdm = document.createElement("td");

        pop.appendChild(popText);
        dwdm.appendChild(dwdmText);
        tr.appendChild(pop);
        tr.appendChild(dwdm);

        table.appendChild(tr);
    }
}

/*-----------------------Event Listeners-----------------------*/

// POP Input Boxes
document.getElementById('pop1Input').addEventListener('blur', function(){ validatePopCode('pop1Input', 'pop1' ) });
document.getElementById('pop2Input').addEventListener('blur', function () { validatePopCode('pop2Input', 'pop2') });
document.getElementById('pop1Input').addEventListener('change', generateCoinPath);
document.getElementById('pop2Input').addEventListener('change', generateCoinPath);

// Reset Button
document.getElementById('resetCoinPath').addEventListener('click', resetCoin);

// Question Mark/POP table button
document.getElementById('openTable').addEventListener('click', generateDwdmTable);
