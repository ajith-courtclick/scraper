from src.ecourts_scraper import ECourtsScraper

def main():
    # Your example HTML
    html_content = '''<main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 maincontentDiv">
         <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-0 mb-2">
            <div class="col p-2 alert alert-primary alert-dismissible fade show d-block" role="alert">
               Download eCourts Services App :&nbsp;&nbsp;<a onclick="externalLink('https://play.google.com/store/apps/details?id=in.gov.ecourts.eCourtsServices')" rel="noopener noreferrer" title="Google play External website that opens a new window" tabindex="0"><img class="AppLogo gp-b" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHkAAAAkAQMAAACXJAcjAAAAA1BMVEX///+nxBvIAAAAAXRSTlMAQObYZgAAAA9JREFUeNpjYBgFo4C2AAACZAABt2QzvQAAAABJRU5ErkJggg==" height="25" alt="Google Play"></a>&nbsp;&nbsp;&nbsp;&nbsp;<a onclick="externalLink('https://appsto.re/in/yv-jlb.i')" rel="noopener noreferrer" title="App Store External website that opens a new window" tabindex="0"><img class="AppLogo app-store-b" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGgAAAAkAQMAAABfSO31AAAAA1BMVEX///+nxBvIAAAAAXRSTlMAQObYZgAAAA5JREFUeNpjYBgFIxEAAAH4AAF2a/E1AAAAAElFTkSuQmCC" height="25" alt="Google Play"></a>
			   <p class="d-inline text-danger ms-2">Do not use browser toolbar reload or back button</p>
               <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
         </div>
         <div class="row  cnr-bg1 CNRBox justify-content-between align-items-center m-0" id="cnr_div" style="display: none;">
            <div class="col-md-6 border rounded shadow text-center py-4 my-3 bg-light m-0 mx-auto">
               <form name="" autocomplete="off">
                  <h1 class="h1class" tabindex="0">Search by CNR number</h1>
                  <p tabindex="0">Enter CNR Number, for example MHAU019999992015</p>
                  <input class="form-control form-control-lg mb-2 cinumber" type="text" placeholder="Enter 16 digit CNR number" aria-label="Enter 16 digit CNR number" name="cino" id="cino" maxlength="16" required="" onkeypress="return /[0-9a-zA-Z]/i.test(event.key)">
                  <br>
				                   <div class="row px-3">
                     <label for="" class="capLabel col-md-auto col-form-label font-weight-bold text-lg-end">Captcha</label>
                     <div id="div_captcha_cnr" class="col-md-auto row"><div class="form-inline text-left">
		<div style="">
		
					<img style="padding-right: 0px;border:1px solid #ccc;" id="captcha_image" src="/ecourtindia_v6/vendor/securimage/securimage_show.php?ed331225f4591a2784f1f692f6bae45a" alt="CAPTCHA Image" tabindex="0" width="120"><div id="captcha_image_audio_div" style="display:inline">
<audio id="captcha_image_audio" preload="none" style="display: none">
<source id="captcha_image_source_wav" src="/ecourtindia_v6/vendor/securimage/securimage_play.php?id=67d534045a0d8" type="audio/wav">
</audio>
</div>
<div id="captcha_image_audio_controls" style="display:inline-block;">
<a tabindex="0" class="captcha_play_button" href="/ecourtindia_v6/vendor/securimage/securimage_play.php?id=67d534045a0e9" onclick="return false">
<img class="captcha_play_image speaker-btn" height="34" width="39" src="images/speaker-btn.jpg" alt="Play CAPTCHA Audio" style="border: 0px">
<img class="captcha_loading_image rotating loading" height="34" width="39" src="/ecourtindia_v6/vendor/securimage/images/refresh-btn.jpg" alt="Loading audio" style="display: none">
</a>
<noscript>Enable Javascript for audio controls</noscript>
</div>
<script type="text/javascript" src="/ecourtindia_v6/vendor/securimage/securimage.js"></script>
<script type="text/javascript">captcha_image_audioObj = new SecurimageAudio({ audioElement: 'captcha_image_audio', controlsElement: 'captcha_image_audio_controls' });</script>
&nbsp;<a tabindex="0" style="border: 0" href="#" title="Refresh Image" onclick="refreshCaptcha()"><img class="refresh-btn" height="34" width="38" src="images/refresh-btn.jpg" alt="Refresh Image" style="border: 0px; vertical-align: bottom;margin-bottom: 6px;"></a></div></div></div>
                     <label for="fcaptcha_code" class="col-md-auto col-form-label text-lg-right font-weight-bold">Enter Captcha</label>
                     <input type="text" class="col-md-auto form-control w-125" id="fcaptcha_code" name="fcaptcha_code" maxlength="6" placeholder="Enter Captcha" autocomplete="off">
                  </div>
				                  <br>
                  <button class="btn btn-primary" type="button" id="searchbtn" onclick="funViewCinoHistory();">Search</button>
                  <button class="btn btn-secondary" type="button" onclick="resetCNR()">Reset</button>
               </form>
            </div>
            <p class="text-white p-2 m-0 CNRNote" aria-hidden="true">Note : If you don\'t have CNR Number then use other options from Search Menu section\'</p>
         </div>
		<p class="text-center m-0"><button class="btn btn-primary px-2 my-2 mx-auto" onclick="main_back('cnr')" id="main_back_cnr" type="button" style="">Back</button></p>
         <div id="history_cnr" style=""><h2 class="h4 text-center  mb-1" tabindex="0" id="chHeading">Munsiffss Court Kuthuparamba</h2>
			<h3 class="h2class fw-bold text-center">Case Details</h3><table class="table case_details_table table-bordered">
						<tbody>
					<tr>
						<td><label class="fw-bold"> </label>Case Type</td>
						<td colspan="3" class="fw-bold text-uppercase">RCP - RENT CONTROL PETITION</td>
					</tr>
					<tr>
						<td><label class="fw-bold"> Filing Number </label></td>
						<td class="fw-bold">1/2019 &nbsp;</td>
						<td><label class="fw-bold">Filing Date</label></td>
						<td class="fw-bold">  01-01-2019  &nbsp;</td>
					</tr>
					<tr>
						<td><label class="fw-bold">Registration Number</label></td>
						<td><label style="font-weight:bold;">3/2019</label></td>
						<td><label style="font-weight:bold;">Registration Date:</label></td>
						<td><label style="font-weight:bold;">23-01-2019</label></td>
					</tr><tr>
						<td><b><label style="font-weight:bold;">CNR Number</label></b></td>
						<td colspan="2"><span class="fw-bold text-uppercase fs-5 me-2 text-danger">KLKN220000012019</span><em class="fw-bold text-dark"> (Note the CNR number for future reference)</em></td><td><a class="fw-bold text-underline text-success fst-italic" href="#" onclick="display_case_acknowlegement('home/case_acknowlegement&amp;cino=KLKN220000012019&amp;state_code=4&amp;dist_code=3&amp;court_code=13&amp;court_complex_code=&amp;national_court_code=KLKN22')"><em style="color:#0e9631;text-decoration:underline;">View QR Code / Cause Title</em></a></td></tr></tbody>
			</table><h3 class="h2class fw-bold text-center mt-2 text-danger">Case Status</h3>
			<table class="table case_status_table table-bordered">
				<tbody>
					<tr>
						<td><label>First Hearing Date</label></td>
						<td colspan="3">13th February 2019</td>
					</tr><tr><td><label><strong>Decision Date</strong></label></td><td colspan="3"><strong>22nd October 2021</strong></td></tr><tr><td><label><strong>Case Status </strong></label></td><td colspan="3"><strong>Case disposed</strong></td></tr><tr><td><label><strong>Nature of Disposal</strong></label></td><td colspan="3"><label><strong>Contested--PARTLY ALLOWED</strong></label></td></tr><tr><td><label><strong>Court Number and Judge</strong></label></td><td colspan="3"><label><strong> 1-MUNSIFF</strong></label></td></tr></tbody></table><h3 class="h2class fw-bold text-center mt-2 text-dark">Petitioner and Advocate</h3>
						<table class="table table-bordered Petitioner_Advocate_table">
							<tbody>
								<tr>
									<td>1) Valiyavalappil Chakkarayan Sujatha, D/o Bhaskaran, Amruthas, Pazhassi amsom Mattannur desom<br>&nbsp;&nbsp;&nbsp;Advocate- K.Rajeevan<br></td></tr>
							</tbody>
						</table><h3 class="h2class fw-bold text-center mt-2 text-dark">Respondent and Advocate</h3>
						<table class="table table-bordered Respondent_Advocate_table">
							<tbody><tr>	<td>1) Akolath Ramesan, D/o Dhamodharan, Akolath House,Keezhallur amsom Peravoor desom </td></tr>
							</tbody>
						</table><br><h3 class="h2class fw-bold text-center mt-2 text-dark">Acts</h3><table class="table acts_table table-bordered " border="1" id="act_table"><tbody><tr><th class="fw-bold">Under Act(s)</th>
											 <th class="fw-bold">Under Section(s)</th></tr><tr><td width="50%" align="left">Procedure Code  \</td><td width="50%" align="left">Sec.5</td></tr></tbody></table><h2 class="h2class" style="font-weight:bold;display:block;clear:both;text-align: center;">IA Status</h2><table class="IAheading" border="1" style=" width:100%;"><tbody><tr><th><b>IA Number </b></th><th><b>Party Name </b></th><th><b>Date of Filing  </b></th><th><b>Next Date  </b><br><b>(Purpose)   </b></th><th><b>IA Status </b></th></tr><tr><td align="left" width="30%">IA/1/2021   </td><td>Valiyavalappil Chakkarayan Sujatha, D/o Bhaskaran, Amruthas, Pazhassi amsom Mattannur desom<br>Akolath Ramesan, D/o Dhamodharan, Akolath House,Keezhallur amsom Peravoor desom<br></td><td>22-03-2021 </td><td>14-07-2021 <br>(Call on)</td><td>Disposed</td></tr></tbody></table><br><table id="historyheading" width="100%" style="text-align:center"><tbody><tr><td><h2 class="h2class" style="clear:both;font-weight:bold;text-align:center;">Case History</h2></td></tr></tbody></table><table width="100%" class="history_table table " align="center" border="1"><thead><tr><td scope="col">Judge</td><td scope="col" style="">Business on Date</td><td scope="col">Hearing Date</td><td scope="col">Purpose of Hearing</td></tr></thead><tbody><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20190313','KLKN220000012019','4','DisposedP','13-02-2019','1','KLKN22','cnr','1')">13-02-2019</a></td><td>13-03-2019</td><td> For counter</td></tr><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20190603','KLKN220000012019','4','DisposedP','13-03-2019','1','KLKN22','cnr','2')">13-03-2019</a></td><td>03-06-2019</td><td> Call on</td></tr><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20190726','KLKN220000012019','4','DisposedP','03-06-2019','1','KLKN22','cnr','3')">03-06-2019</a></td><td>26-07-2019</td><td> Call on</td></tr><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20190919','KLKN220000012019','4','DisposedP','26-07-2019','1','KLKN22','cnr','4')">26-07-2019</a></td><td>19-09-2019</td><td> Call on</td></tr><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20191104','KLKN220000012019','4','DisposedP','19-09-2019','1','KLKN22','cnr','5')">19-09-2019</a></td><td>04-11-2019</td><td> Call on</td></tr><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20191218','KLKN220000012019','4','DisposedP','04-11-2019','1','KLKN22','cnr','6')">04-11-2019</a></td><td>18-12-2019</td><td> Call on</td></tr><tr><td align="left">Munsiff/JFCM No.2, Kuthuparamba</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20200106','KLKN220000012019','4','DisposedP','18-12-2019','1','KLKN22','cnr','7')">18-12-2019</a></td><td>06-01-2020</td><td> Call on</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20200312','KLKN220000012019','4','DisposedP','06-01-2020','1','KLKN22','cnr','8')">06-01-2020</a></td><td>12-03-2020</td><td> Call on</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20200603','KLKN220000012019','4','DisposedP','12-03-2020','1','KLKN22','cnr','9')">12-03-2020</a></td><td>03-06-2020</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20200724','KLKN220000012019','4','DisposedP','03-06-2020','1','KLKN22','cnr','10')">03-06-2020</a></td><td>24-07-2020</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20200917','KLKN220000012019','4','DisposedP','24-07-2020','1','KLKN22','cnr','11')">24-07-2020</a></td><td>17-09-2020</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20201031','KLKN220000012019','4','DisposedP','17-09-2020','1','KLKN22','cnr','12')">17-09-2020</a></td><td>31-10-2020</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20201201','KLKN220000012019','4','DisposedP','31-10-2020','1','KLKN22','cnr','13')">31-10-2020</a></td><td>01-12-2020</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20210202','KLKN220000012019','4','DisposedP','01-12-2020','1','KLKN22','cnr','14')">01-12-2020</a></td><td>02-02-2021</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20210322','KLKN220000012019','4','DisposedP','02-02-2021','1','KLKN22','cnr','15')">02-02-2021</a></td><td>22-03-2021</td><td> For Steps</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20210524','KLKN220000012019','4','DisposedP','22-03-2021','1','KLKN22','cnr','16')">22-03-2021</a></td><td>24-05-2021</td><td> For commission report</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20210618','KLKN220000012019','4','DisposedP','24-05-2021','1','KLKN22','cnr','17')">24-05-2021</a></td><td>18-06-2021</td><td> For commission report</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20210714','KLKN220000012019','4','DisposedP','18-06-2021','1','KLKN22','cnr','18')">18-06-2021</a></td><td>14-07-2021</td><td> For commission report</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20210727','KLKN220000012019','4','DisposedP','14-07-2021','1','KLKN22','cnr','19')">14-07-2021</a></td><td>27-07-2021</td><td> For objection to CR</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20211001','KLKN220000012019','4','DisposedP','27-07-2021','1','KLKN22','cnr','20')">27-07-2021</a></td><td>01-10-2021</td><td> LISTED FOR TRIAL</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20211004','KLKN220000012019','4','DisposedP','01-10-2021','1','KLKN22','cnr','21')">01-10-2021</a></td><td>04-10-2021</td><td> call with connected case</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20211006','KLKN220000012019','4','DisposedP','04-10-2021','1','KLKN22','cnr','22')">04-10-2021</a></td><td>06-10-2021</td><td> call with connected case</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','20211022','KLKN220000012019','4','DisposedP','06-10-2021','1','KLKN22','cnr','23')">06-10-2021</a></td><td>22-10-2021</td><td> call with connected case</td></tr><tr><td align="left">MUNSIFF</td><td align="left"><a href="#" onclick="viewBusiness('13','3','','KLKN220000012019','4','Disposed','22-10-2021','1','KLKN22','cnr','0')">22-10-2021</a></td><td></td><td> Disposed</td></tr></tbody></table><table id="orderheading" align="center"><tbody><tr><td><br><h2 class="h2class" style="font-weight:bold;">Final Orders / Judgements  </h2></td></tr></tbody></table><table width="100%" class="order_table table " align="center" border="1"><tbody><tr><td><strong>&nbsp;&nbsp;Order Number</strong></td><td><strong>&nbsp;&nbsp;Order Date </strong></td><td> <strong>&nbsp;&nbsp;Order Details </strong></td></tr><tr><td>&nbsp;&nbsp;1</td><td style="border-top:none;">&nbsp;&nbsp;22-10-2021</td><td style=" border-top:none;" colspan="3"><a href="#" onclick="displayPdf('home/display_pdf&amp;filename=/orders/2019/201500000032019_1.pdf&amp;caseno=RCP/3/2019&amp;court_code=13&amp;appFlag=&amp;normal_v=1')"><font color="green"> &nbsp;&nbsp;Order </font><span></span></a></td></tr></tbody></table></div>
		 <div id="caseBusinessDiv_cnr" style="display:none"></div>
         <div class="row mt-2" id="help_cnr" style="display: none;">
            <div class="col">
               <h1 class="bg-primary fw-bold text-white howtotext rounded p-1"><i class="fa fa-question-circle" aria-hidden="true"></i>&nbsp;How to </h1>
               <ul class="list-group list-group-numbered">
                  <li class="list-group-item"><a rel="noopener noreferrer" href="/ecourtindia_v6/?p=view_help_videos/show_help_videos&amp;caseSearchType=CNRHelp&amp;app_token=2469950d4e388c4e0f8f5a24725a88178d48eb1f95e3e42a822db49d0bbcdc9f">Click here to view help video</a></li>
                  <li class="list-group-item">Enter the 16 digit alphanumeric CNR Number without any hyphen or space</li>
                  <li class="list-group-item">Click Search button to view current status and history of the case</li>
                  <li class="list-group-item">If you don't know the CNR number of the case, click on the Case Status icon on the left menu to search the case with other options like case registration number, party name, advocate name etc.</li>
               </ul>
            </div>
         </div>
      </main>'''

    # Initialize scraper and test parse
    scraper = ECourtsScraper()
    case_details = scraper.test_parse_html(html_content)

if __name__ == "__main__":
    main() 