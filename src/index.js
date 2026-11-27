import {
  MIN_BATCH_PUBLISHES,
  MAX_BATCH_PUBLISHES,
  MAX_BATCH_ATTEMPTS,
  MAX_IN_FLIGHT_BATCH_RENDERS,
  shouldFillBatch,
  batchCompletionStatus
} from "./render-batch-policy.mjs";

const VERSION = "GTA6-FACTORY-6.3-FIRST-LIVE-BATCH";
// The [initial-production] deployment marker runs one permission-gated bootstrap cycle after deploy.
const MIN_AUTOMATIC_PUBLISHES_PER_CYCLE = MIN_BATCH_PUBLISHES;
const MAX_AUTOMATIC_RENDERS_PER_CYCLE = MAX_BATCH_PUBLISHES;
const MAX_AUTOMATIC_ATTEMPTS_PER_CYCLE = MAX_BATCH_ATTEMPTS;

const HTML = String.raw`<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GTA6 Shorts Factory 5.2</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b0d12;color:#e8eaf0;font:14px Arial}main{max-width:1150px;margin:30px auto;padding:0 16px}h1{font-size:27px}h2{font-size:18px;margin-top:25px}.panel{background:#141923;border:1px solid #293243;border-radius:12px;padding:18px;margin:14px 0}.muted{color:#9299a8}button{background:#8b5cf6;color:white;border:0;padding:11px 15px;border-radius:7px;cursor:pointer;margin:4px;font-weight:bold}.secondary{background:#30394a}input{background:#0d1119;border:1px solid #343d4d;color:white;padding:11px;border-radius:7px;width:100%;margin:7px 0}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}.stat{background:#0e131d;padding:15px;border-radius:9px}.stat strong{display:block;font-size:26px;margin-top:8px}.notice{background:#202b3a;padding:12px;border-radius:8px;margin-top:12px;white-space:pre-wrap}.hidden{display:none}.status-ok{color:#86efac;font-weight:bold}.status-warn{color:#facc15;font-weight:bold}.status-bad{color:#f87171;font-weight:bold}.mini{font-size:12px;color:#9aa3b2}.wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #293140;vertical-align:top}th{color:#aeb8ca}textarea{width:100%;min-height:300px;background:#0d1119;color:white;border:1px solid #343d4d;padding:10px;border-radius:7px;line-height:1.5}a{color:#b69aff}.detail-box{background:#0e131d;border:1px solid #30394a;border-radius:9px;padding:15px;margin-top:12px}.detail-box h3{margin-top:0}.view-button{background:#30394a}.button-link{display:inline-block;background:#166534;color:white;text-decoration:none;padding:8px 11px;border-radius:7px;font-weight:600;font-size:13px}.draft-select{width:18px;height:18px;accent-color:#8b5cf6}
</style></head><body><main>
<h1>GTA6 SHORTS FACTORY</h1><div class="muted">GTA6-FACTORY-5.7 · Offline Editorial Review · Twitch Clip Discovery · Shorts Render · YouTube Publishing</div>
<section id="login" class="panel hidden"><h2>Panel girişi</h2><input id="password" type="password" placeholder="APP_PASSWORD"><button id="loginBtn">Giriş yap</button><div id="loginMsg" class="notice hidden"></div></section>
<div id="app" class="hidden">
<section class="panel" id="quickClipPanel" style="border:2px solid #16a34a;background:#102019;padding:22px"><h2 style="margin-top:0">TWITCH KLİBİNİ FABRİKAYA GÖNDER</h2><p class="muted">Fabrika GTA VI kliplerini Twitch'te otomatik keşfeder, herkese açık klipleri indirir, 9:16 Shorts'a dönüştürür ve YouTube kanalına public olarak yükler. Aynı klip ikinci kez yayınlanmaz.</p><input id="quickClipUrl" type="url" placeholder="https://www.twitch.tv/.../clip/..."><button id="quickClipProduce" style="width:100%;padding:15px;font-size:15px;background:#16a34a">FABRİKAYA GÖNDER VE YAYINLA</button><div id="quickClipResult" class="notice hidden"></div></section>

<section class="panel"><div class="stats"><div class="stat">Twitch kaynakları<strong id="sources">0</strong></div><div class="stat">Üretim kuyruğu<strong id="queued">0</strong></div><div class="stat">Hazırlanan Shorts<strong id="drafts">0</strong></div><div class="stat">YouTube yayınları<strong id="published">0</strong></div></div><p class="muted">Otomatik Twitch keşfi → MP4 render → İngilizce SEO → YouTube public upload.</p><button id="refresh" class="secondary">Paneli yenile</button><button id="discover">GTA VI Twitch keşfini başlat</button><button id="prepare">PAKETLERİ OLUŞTUR / GÜNCELLE</button><button id="logout" class="secondary">Çıkış</button><div id="msg" class="notice hidden"></div></section>
<section class="panel"><h2>Bulut bağlantıları</h2><div id="systemStatus" class="notice">Bağlantılar kontrol ediliyor...</div><p class="muted">Gizli anahtarların değerleri gösterilmez; yalnızca yapılandırılmış olup olmadıkları kontrol edilir.</p></section>
<section class="panel"><h2>Twitch kaynak alma</h2><p class="muted">GTA VI klipleri Twitch API ile otomatik keşfedilir. Herkese açık klipler yt-dlp ile doğrudan alınır; indirilemeyen kaynaklar atlanır ve sonraki kliplere geçilir. Üretim ve public YouTube yüklemesi üç saatte bir otomatik yürütülür.</p></section>

<section class="panel"><h2>Manuel kaynak ekle</h2><input id="url" placeholder="Klip URL"><input id="creator" placeholder="Yayıncı adı"><input id="title" placeholder="Klip başlığı"><button id="add">Kaynak ekle</button></section>
<section class="panel"><h2>Kaynaklar</h2><div class="wrap"><table><thead><tr><th>Yayıncı / Klip</th><th>Puan</th><th>Medya analizi</th><th>GTA VI durumu</th><th>Kaynak</th></tr></thead><tbody id="sourceRows"></tbody></table></div></section>
<section class="panel" id="creatorRightsPanel" style="border:1px solid #8b5cf6">
<h2>Yayıncı ve oyun görüntüsü kullanım izinleri</h2>
<p class="muted">Twitch MP4 indirme izni, YouTube'da yeniden yayınlama izni değildir. Her yayıncı için yazılı kullanım izni kanıtı, izin verilen azami kaynak süresi ve GTA VI oyun görüntüsü için ayrı hak dayanağı kaydedilmeden otomatik yayın yapılmaz.</p>
<div class="detail-box">
<label for="permissionBroadcasterId">Twitch yayıncı ID</label><input id="permissionBroadcasterId" placeholder="Kaynak tablosundaki broadcaster ID">
<label for="permissionBroadcasterName">Yayıncı adı</label><input id="permissionBroadcasterName" placeholder="Twitch kullanıcı adı">
<label for="permissionCreatorEvidence">Yayıncının video/YouTube yeniden kullanım izni kanıtı</label><input id="permissionCreatorEvidence" placeholder="Yazılı izin bağlantısı veya kayıt referansı">
<label for="permissionAudioEvidence">Yayıncı sesi ve videodaki müzik/diğer seslerin YouTube kullanım hakkı kanıtı</label><input id="permissionAudioEvidence" placeholder="Müzik lisansı, ses izni veya sessiz/müziksiz kullanım teyidi referansı">
<label style="display:flex;gap:8px;align-items:flex-start;margin:10px 0"><input id="permissionAudioConfirm" type="checkbox" style="width:auto;margin:2px 0"> Bu klibin yayıncı sesi ve tüm arka plan müzikleri YouTube'da yeniden kullanım için lisanslı/izinli; aksi durumda kaynak reddedilecek.</label>
<label for="permissionMaxSeconds">İzin verilen en uzun kaynak kullanım süresi (saniye)</label><input id="permissionMaxSeconds" type="number" min="45" max="175" value="60">
<label for="permissionExpiry">İzin bitiş tarihi (isteğe bağlı)</label><input id="permissionExpiry" type="datetime-local">
<label for="permissionGameBasis">GTA VI oyun görüntüsü için hak dayanağı</label>
<select id="permissionGameBasis" style="width:100%;padding:11px;background:#0d1119;color:white;border:1px solid #343d4d;border-radius:7px;margin:7px 0">
<option value="rockstar_noncommercial_guidelines">Yalnızca Rockstar'ın non-commercial fan kullanım koşulları</option>
<option value="publisher_written_permission">Rockstar/Take-Two yazılı kullanım lisansı/izni</option>
</select>
<label for="permissionGameEvidence">Rockstar/Take-Two yazılı izin kanıtı (bu seçenek seçildiyse zorunlu)</label><input id="permissionGameEvidence" placeholder="https://... veya izin kayıt referansı">
<label style="display:flex;gap:8px;align-items:flex-start;margin:10px 0"><input id="permissionNoncommercial" type="checkbox" style="width:auto;margin:2px 0"> Kanalın/video kullanımının ticari olmadığını, monetized/promosyon amacı taşımadığını ve Rockstar'ın saydığı istisnalara girmediğini teyit ediyorum.</label>
<label for="permissionNotes">Notlar / özel kapsam</label><textarea id="permissionNotes" rows="2" style="min-height:70px"></textarea>
<label style="display:flex;gap:8px;align-items:flex-start;margin:10px 0"><input id="permissionConfirm" type="checkbox" style="width:auto;margin:2px 0"> İzin kanıtlarını kontrol ettim; kullanım platformu YouTube, süre sınırı ve kullanım kapsamı doğru.</label>
<button type="button" id="saveCreatorPermission">İZİN KAYDINI ONAYLA</button>
<div id="permissionMessage" class="notice hidden"></div>
</div>
<div class="wrap"><table><thead><tr><th>Yayıncı</th><th>Durum</th><th>Görüntü/ses izni</th><th>Hak dayanağı</th><th>İşlem</th></tr></thead><tbody id="permissionRows"></tbody></table></div>
</section>
<section class="panel"><h2>Shorts üretim paketleri</h2><p class="muted">GTA VI olduğu doğrulanan kaynaklardan paketler otomatik hazırlanır. Kaynakları seçip topluca MP4 üretebilir, hazır olanları indirebilirsin.</p><div style="display:flex;gap:8px;flex-wrap:wrap;margin:12px 0"><button type="button" id="selectAllDrafts" class="secondary">Tümünü seç</button><button type="button" id="clearDraftSelection" class="secondary">Seçimi temizle</button><button type="button" id="renderSelectedDrafts">SEÇİLENLERİ MP4 ÜRET</button></div><div id="bulkRenderStatus" class="notice hidden"></div><div class="wrap"><table><thead><tr><th>Seç</th><th>Kaynak</th><th>Başlık</th><th>Durum</th><th>İşlem</th></tr></thead><tbody id="draftRows"></tbody></table></div></section>
<section class="panel" id="youtubeKit" style="border:1px solid #394150">
<h2>YouTube Kanal ve SEO Merkezi</h2>
<p class="muted">Kanal adını ve marka kimliğini sen belirleyeceksin. Bu bölüm kanal açıklaması, anahtar kelimeler ve her Shorts için İngilizce SEO paketi hazırlamak içindir.</p>
<div class="detail-box"><h3>Kanal açıklaması (About)</h3>
<textarea id="vrChannelAbout" style="min-height:130px">Welcome to VI RUSH — your destination for Grand Theft Auto VI (GTA 6) Shorts. Explore memorable moments from Leonida, intense encounters, surprising gameplay details, funny reactions and cinematic scenes. Every clip is selected and edited for a quick, focused watch, with creator credit and source context. Subscribe for more GTA VI moments.</textarea>
<button type="button" class="secondary" id="vrCopyAbout">KANAL AÇIKLAMASINI KOPYALA</button>
<h3>Varsayılan kanal anahtar kelimeleri</h3>
<textarea id="vrChannelKeywords" style="min-height:85px">GTA 6, GTA VI, Grand Theft Auto VI, GTA 6 gameplay, GTA 6 clips, GTA 6 moments, GTA 6 shorts, gaming shorts, Vice City, Leonida, Rockstar Games</textarea>
<button type="button" class="secondary" id="vrCopyKeywords">KANAL ANAHTAR KELİMELERİNİ KOPYALA</button></div>
<h3>Shorts SEO paketi oluştur</h3>
<input id="vrVideoSubject" placeholder="Klipte ne oluyor? (örn. police chase gone wrong)">
<input id="vrVideoHook" placeholder="Öne çıkarılacak detay (isteğe bağlı)">
<input id="vrVideoCredit" placeholder="Kaynak / yayıncı adı (isteğe bağlı)">
<div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" id="vrGenerateSeo">SEO PAKETİNİ OLUŞTUR</button><button type="button" class="secondary" id="vrCopyAllSeo">TÜM SEO PAKETİNİ KOPYALA</button></div>
<label for="vrSeoTitle">Başlık (100 karaktere uygun)</label><input id="vrSeoTitle">
<label for="vrSeoDescription">Açıklama</label><textarea id="vrSeoDescription" style="min-height:140px"></textarea>
<label for="vrSeoTags">Etiketler (virgülle ayrılmış)</label><textarea id="vrSeoTags" style="min-height:85px">GTA 6, GTA VI, Grand Theft Auto VI, GTA 6 gameplay, GTA 6 clips, GTA 6 moments, GTA 6 shorts, gaming shorts, Vice City, Leonida, Rockstar Games</textarea>
<label for="vrSeoHashtags">Hashtag'ler</label><input id="vrSeoHashtags" value="#GTA6 #GTAVI #GTAVIGameplay #GamingShorts #Shorts">
<p class="mini">Başlık ve açıklamalar İngilizce/ABD kitlesine göre hazırlanır. Yanıltıcı etiket, sahte trend veya doğrulanmamış bilgi eklenmez.</p>
</section>
<section class="panel" id="detailPanel"><h2>Üretim paketi detayları</h2><div id="detail" class="muted">Bir pakette Görüntüle seç.</div></section>
</div></main>
<script>
const $=id=>document.getElementById(id);let currentData=null,quickClipDraftId=null;
async function api(path,body){const options={method:body?"POST":"GET",headers:{"Content-Type":"application/json"}};if(body)options.body=JSON.stringify(body);const response=await fetch(path,options);let data;try{data=await response.json()}catch{throw new Error("Sunucudan geçersiz yanıt geldi.")}if(!response.ok)throw new Error(data.error||"İşlem başarısız");return data;}
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function showMsg(t){$("msg").textContent=t;$("msg").classList.remove("hidden");}
function renderQuickClipDownload(){const box=$("quickClipDownloadStatus");if(!box)return;const drafts=currentData&&Array.isArray(currentData.drafts)?currentData.drafts:[];const d=quickClipDraftId?drafts.find(x=>String(x.id)===String(quickClipDraftId)):(drafts[0]||null);if(d&&!quickClipDraftId)quickClipDraftId=d.id;if(!d){box.textContent="Henüz bu bölümden bir klip üretimi başlatılmadı.";return;}const status=String(d.job_status||d.status||"queued_review");if(status==="ready"&&d.output_key){const direct=String(d.output_key).toLowerCase().endsWith(".mp4");box.innerHTML="<b>MP4 hazır.</b>"+(direct?"<p><a target=\"_blank\" rel=\"noopener\" href=\""+esc(d.output_key)+"\">MP4 DOSYASINI İNDİR</a></p>":"")+(d.package_url||(!direct?d.output_key:"")?"<p><a target=\"_blank\" rel=\"noopener\" href=\""+esc(d.package_url||d.output_key)+"\">TÜM DOSYALARI ZIP İNDİR</a></p>":"")+"<span class=\"mini\">ZIP içinde video, TXT açıklama paketi, kapak ve kanal marka dosyaları bulunur.</span>";}else if(status==="failed"){box.innerHTML="<b>Üretim başarısız.</b><p>"+esc(d.last_error||"GitHub Actions iş ayrıntılarını açıp hatayı kontrol et.")+"</p>"+(d.output_key?"<a target=\"_blank\" rel=\"noopener\" href=\""+esc(d.output_key)+"\">Render işini aç</a>":"");}else{box.innerHTML="<b>MP4 hazırlanıyor.</b><p>Durum: "+esc(status)+"</p><span class=\"mini\">Render tamamlandığında indirme bağlantısı burada görünecek. Yenile düğmesine bas.</span>";}}
function showDraft(id){const drafts=currentData&&Array.isArray(currentData.drafts)?currentData.drafts:[];const d=drafts.find(x=>String(x.id)===String(id));if(!d){$("detail").innerHTML="<div class='status-bad'>Paket bulunamadı. Paneli yenileyip tekrar dene.</div>";$("detailPanel").scrollIntoView({behavior:"smooth",block:"start"});return;}
$("detail").innerHTML="<div class='detail-box'><h3>"+esc(d.title||"Başlıksız paket")+"</h3><p><b>Yayıncı:</b> "+esc(d.creator_name||"Bilinmiyor")+"</p><p><b>Durum:</b> "+esc(d.status||"-")+"</p><p><b>Paket ID:</b> <span class='mini'>"+esc(d.id)+"</span></p><h3>Üretim metni</h3><textarea id='draftScript' readonly></textarea><p><a target='_blank' rel='noopener' href='"+esc(d.source_url||"#")+"'>Kaynak klibi aç</a></p><button type='button' id='copyDraft' class='secondary'>Metni kopyala</button><button type='button' id='renderDraft'>MP4 üret</button><p class='mini'>Render: <b>"+esc(d.job_status||d.status||"queued_review")+"</b></p>"+(d.output_key?"<p><a target='_blank' rel='noopener' href='"+esc(d.output_key)+"'>MP4 DOSYASINI İNDİR</a></p>":"")+(d.package_url?"<p><a target='_blank' rel='noopener' href='"+esc(d.package_url)+"'>TÜM DOSYALARI ZIP İNDİR</a></p>":"")+"<p class='mini'>YouTube: <b>"+esc(d.youtube_status||"not_run")+"</b></p>"+(d.youtube_url?"<p><a target='_blank' rel='noopener' href='"+esc(d.youtube_url)+"'>YouTube videosunu aç (public)</a></p>":"")+"<p id='renderResult' class='mini'></p></div>";$("draftScript").value=d.script||"Bu pakette henüz metin bulunmuyor.";
$("copyDraft").onclick=async()=>{try{await navigator.clipboard.writeText($("draftScript").value);showMsg("Üretim metni panoya kopyalandı.")}catch(e){$("draftScript").select();showMsg("Metin seçildi. CTRL+C ile kopyalayabilirsin.")}};$("renderDraft").onclick=async()=>{const b=$("renderDraft");b.disabled=true;b.textContent="Render başlatılıyor...";try{const r=await api("/api/render/dispatch",{draft_id:d.id});$("renderResult").textContent="Bulut render işi başlatıldı. İş: "+r.job_id+" · Durum: "+r.status;showMsg("MP4 üretimi buluta gönderildi.");await refresh()}catch(e){$("renderResult").textContent=e.message;showMsg(e.message)}finally{b.disabled=false;b.textContent="MP4 üret"}};$("detailPanel").scrollIntoView({behavior:"smooth",block:"start"});}
async function loadPermissions(){
 try{
  const result=await api("/api/permissions");
  const list=result.permissions||[];
  $("permissionRows").innerHTML=list.map(p=>{
   const expiry=p.permission_expires_at||"No expiry recorded";
   const basis=p.game_rights_basis==="publisher_written_permission"?"Written publisher licence":"Non-commercial Rockstar policy";
   const status=p.permission_status==="approved"?"APPROVED":p.permission_status;
   const safeId=esc(p.broadcaster_id);
   return "<tr><td><b>"+esc(p.broadcaster_name)+"</b><br><span class='mini'>"+safeId+"</span></td><td>"+esc(status)+"</td><td>Max source: "+esc(p.max_source_seconds)+"s<br>"+esc(expiry)+"<br>Video: "+esc(p.creator_permission_evidence)+"<br>Audio/music: "+esc(p.audio_rights_evidence||"missing")+"</td><td>"+esc(basis)+(p.game_rights_evidence_reference?"<br>"+esc(p.game_rights_evidence_reference):"")+"</td><td><button type='button' class='secondary' data-revoke-permission='"+safeId+"'>İZNİ GERİ ÇEK</button></td></tr>";
  }).join("")||"<tr><td colspan='5'>Henüz doğrulanmış kullanım izni kaydı yok. İzin kaydı olmayan yayıncılar otomatik yayın havuzuna alınmaz.</td></tr>";
 }catch(e){$("permissionRows").innerHTML="<tr><td colspan='5'>İzin kayıtları alınamadı: "+esc(e.message)+"</td></tr>";}
}
async function loginCheck(){try{await api("/api/me");$("login").classList.add("hidden");$("app").classList.remove("hidden");await refresh();}catch(e){$("app").classList.add("hidden");$("login").classList.remove("hidden");}}
async function refresh(){try{let system=null;try{system=await api("/api/system/status")}catch(e){}if(system){const checks=[["Cloudflare D1",system.database],["Uygulama parolası",system.appPassword],["Twitch API",system.twitchClient],["GitHub Actions",system.githubToken],["Render geri bildirim anahtarı",system.renderWebhookSecret]];$("systemStatus").innerHTML="<p>Worker: <b>"+esc(system.version)+"</b></p>"+checks.map(([name,ok])=>"<p>"+(ok?"<span class='status-ok'>HAZIR</span>":"<span class='status-bad'>EKSİK</span>")+" · "+esc(name)+"</p>").join("")}else{$("systemStatus").textContent="Bulut bağlantı tanılaması yeni Worker dağıtımından sonra kullanılabilir."}currentData=await api("/api/data");await loadPermissions();const s=currentData.sources||[],d=currentData.drafts||[];$("sources").textContent=s.length;$("drafts").textContent=d.length;$("queued").textContent=d.filter(x=>x.status==="queued_review").length;$("published").textContent=d.filter(x=>x.youtube_status==="published_public"&&x.youtube_url).length;
$("sourceRows").innerHTML=s.map(x=>"<tr><td><b>"+esc(x.creator_name)+"</b><br>"+esc(x.title)+(x.relevance_status==="relevant"?"<br><span class='status-ok'>GTA VI kategorisi doğrulandı</span>":"")+"</td><td>"+esc(x.score==null?"-":x.score)+"/100</td><td>"+(x.media_analyzed_at?("Kalite "+esc(x.media_quality_score==null?"-":x.media_quality_score)+"/100<br>"+esc(x.source_width)+"×"+esc(x.source_height)+" · "+esc(x.source_fps)+" FPS<br>"+(x.source_has_audio?"Ses var":"Ses yok")+" · Sessizlik "+esc(Math.round(Number(x.silence_ratio||0)*100))+"%<br>Sahne geçişi: "+esc(x.scene_change_count==null?"-":x.scene_change_count)+" · Ortalama ses: "+esc(x.mean_volume_db==null?"-":x.mean_volume_db+" dB")):"Render analizi bekleniyor")+"</td><td>"+esc(x.relevance_status)+"</td><td><a target='_blank' rel='noopener' href='"+esc(x.source_url)+"'>Klibi aç</a></td></tr>").join("");
$("draftRows").innerHTML=d.map(x=>{const st=String(x.job_status||x.status||"queued_review"),ready=st==="ready"&&!!x.output_key,busy=st==="processing";return "<tr><td><input type='checkbox' class='draft-select' value='"+esc(x.id)+"' "+(ready||busy?"":"checked")+" aria-label='Kaynağı seç'></td><td>"+esc(x.creator_name||"Bilinmiyor")+"</td><td>"+esc(x.title)+"</td><td>"+esc(st)+(x.youtube_status?"<br><span class='mini'>YouTube: "+esc(x.youtube_status)+"</span>":"")+(x.thumbnail_status?"<br><span class='mini'>Kapak: "+esc(x.thumbnail_status)+"</span>":"")+"</td><td><button type='button' class='view-button' data-view='"+esc(x.id)+"'>Görüntüle</button> <button type='button' data-render='"+esc(x.id)+"' "+(ready||busy?"disabled":"")+">"+(ready?"ÜRETİLDİ":busy?"İŞLENİYOR":"MP4 ÜRET")+"</button> "+(ready?(String(x.output_key||"").toLowerCase().endsWith(".mp4")?"<a class='button-link' target='_blank' rel='noopener' href='"+esc(x.output_key)+"'>MP4 İNDİR</a> "+(x.package_url?"<a class='button-link' target='_blank' rel='noopener' href='"+esc(x.package_url)+"'>PAKET ZIP</a>":""):"<a class='button-link' target='_blank' rel='noopener' href='"+esc(x.package_url||x.output_key)+"'>PAKET ZIP İNDİR</a>"):"")+"</td></tr>"}).join("");if(!d.length)$("draftRows").innerHTML="<tr><td colspan='5'>Henüz üretim paketi yok. Önce GTA VI keşfini ve paket oluşturmayı çalıştır.</td></tr>";}catch(e){showMsg(e.message);}}
$("draftRows").addEventListener("click",async e=>{const view=e.target.closest("button[data-view]");if(view){e.preventDefault();e.stopPropagation();showDraft(view.getAttribute("data-view"));return;}const render=e.target.closest("button[data-render]");if(render){const id=render.getAttribute("data-render");render.disabled=true;render.textContent="BAŞLATILIYOR...";try{const r=await api("/api/render/dispatch",{draft_id:id});showMsg(r.already_exists?r.message:"MP4 üretimi başlatıldı. İş: "+r.job_id);await refresh()}catch(err){showMsg(err.message);render.disabled=false;render.textContent="MP4 ÜRET"}}});$("selectAllDrafts").onclick=()=>document.querySelectorAll("#draftRows .draft-select").forEach(x=>x.checked=true);$("clearDraftSelection").onclick=()=>document.querySelectorAll("#draftRows .draft-select").forEach(x=>x.checked=false);$("renderSelectedDrafts").onclick=async()=>{const ids=[...document.querySelectorAll("#draftRows .draft-select:checked")].map(x=>x.value),box=$("bulkRenderStatus"),btn=$("renderSelectedDrafts");if(!ids.length){showMsg("Önce üretilecek kaynakları seç.");return;}btn.disabled=true;box.classList.remove("hidden");let ok=0,failed=0;for(let i=0;i<ids.length;i++){box.textContent="Toplu üretim: "+(i+1)+"/"+ids.length+" hazırlanıyor...";try{const r=await api("/api/render/dispatch",{draft_id:ids[i]});if(r.already_exists&&r.status==="ready")ok++;else if(r.already_exists)ok++;else ok++;}catch(err){failed++;}}box.textContent="Toplu işlem tamamlandı. Başlatılan: "+ok+" · Başlatılamayan: "+failed+". Durum ve indirme bağlantıları aşağıdaki satırlarda gösteriliyor.";btn.disabled=false;await refresh();};
function vrCopy(id){const el=$(id);if(!el)return;const value=el.value||el.textContent||"";navigator.clipboard.writeText(value).then(()=>showMsg("Kopyalandı.")).catch(()=>{el.focus();el.select();showMsg("Metin seçildi; CTRL+C ile kopyala.")});}
$("vrCopyAbout").onclick=()=>vrCopy("vrChannelAbout");
$("vrCopyKeywords").onclick=()=>vrCopy("vrChannelKeywords");
$("vrGenerateSeo").onclick=()=>{const subject=$("vrVideoSubject").value.trim(),hook=$("vrVideoHook").value.trim(),credit=$("vrVideoCredit").value.trim();if(!subject){showMsg("Önce klibin konusunu yaz.");return;}const clean=subject.replace(/[.!?]+$/g,"").trim(),titleBase=(hook?hook+" — ":"")+clean;const title=(titleBase+" | GTA 6 #Shorts").slice(0,100);const description=[clean+" in Grand Theft Auto VI. "+(hook?hook+". ":"")+"Watch till the end and tell us what you think.","\nSubscribe for more GTA VI moments from Leonida.",credit?"\nClip credit: "+credit:"","\n#GTA6 #GTAVI #GamingShorts #Shorts"].filter(Boolean).join("\n");$("vrSeoTitle").value=title;$("vrSeoDescription").value=description;$("vrSeoTags").value="GTA 6, GTA VI, Grand Theft Auto VI, GTA 6 gameplay, GTA 6 clips, GTA 6 moments, GTA 6 shorts, gaming shorts, Vice City, Leonida, Rockstar Games";$("vrSeoHashtags").value="#GTA6 #GTAVI #GamingShorts #Shorts";showMsg("YouTube SEO paketi hazır.");};
$("vrCopyAllSeo").onclick=()=>{const all=["TITLE\n"+$("vrSeoTitle").value,"DESCRIPTION\n"+$("vrSeoDescription").value,"TAGS\n"+$("vrSeoTags").value,"HASHTAGS\n"+$("vrSeoHashtags").value].join("\n\n");navigator.clipboard.writeText(all).then(()=>showMsg("Başlık, açıklama, etiketler ve hashtagler kopyalandı.")).catch(()=>showMsg("Tarayıcı pano izni vermedi."));};$("loginBtn").onclick=async()=>{try{await api("/api/login",{password:$("password").value});$("password").value="";await loginCheck()}catch(e){$("loginMsg").textContent=e.message;$("loginMsg").classList.remove("hidden")}};
$("password").addEventListener("keydown",e=>{if(e.key==="Enter")$("loginBtn").click()});
$("refresh").onclick=async()=>{await refresh();showMsg("Panel yenilendi.")};
$("logout").onclick=async()=>{await api("/api/logout",{});location.reload()};
$("discover").onclick=async()=>{showMsg("GTA VI Twitch keşfi çalışıyor...");try{const r=await api("/api/discover",{});showMsg("GTA VI keşfi tamamlandı"+"\nYayıncı: "+r.creators+"\nAlınan klip: "+r.clips+"\nYeni kaynak: "+r.saved+"\nTekrar kayıt: "+r.duplicates+"\nAlakasız klip atlandı: "+r.filtered+"\nOyun kategorisi: "+(r.game_id?"Doğrulandı":"Başlık filtresi kullanıldı"));await refresh()}catch(e){showMsg(e.message)}};
$("prepare").onclick=async()=>{showMsg("Paketler oluşturuluyor ve mevcut paketler güncelleniyor...");try{const r=await api("/api/prepare",{});showMsg("ÜRETİM HAZIRLIĞI TAMAMLANDI"+"\nKontrol edilen: "+r.checked+"\nYeni paket: "+r.created+"\nGüncellenen paket: "+r.updated+"\nÖnceden mevcut: "+r.existing+"\nAlakasız kaynak atlandı: "+r.skipped_irrelevant+"\nKuyruktaki toplam: "+r.total);await refresh()}catch(e){showMsg(e.message)}};
$("quickClipProduce").onclick=async()=>{const b=$("quickClipProduce"),out=$("quickClipResult"),url=$("quickClipUrl").value.trim();if(!url){out.textContent="Paste a public Twitch clip URL first.";out.classList.remove("hidden");return;}b.disabled=true;b.textContent="SENDING TO FACTORY...";out.textContent="Checking GTA VI category, queueing render and public YouTube upload...";out.classList.remove("hidden");try{const r=await api("/api/source/quick",{url});out.textContent="Factory job started. Job: "+r.job_id+" · Status: "+r.status+". MP4, ZIP and public YouTube link will appear in the dashboard when finished.";showMsg("Clip sent to the factory.");$("quickClipUrl").value="";await refresh()}catch(e){out.textContent=e.message;showMsg(e.message)}finally{b.disabled=false;b.textContent="SEND TO FACTORY & PUBLISH"}};
$("add").onclick=async()=>{try{await api("/api/source/manual",{url:$("url").value,creator:$("creator").value,title:$("title").value});$("url").value="";$("creator").value="";$("title").value="";showMsg("Kaynak eklendi.");await refresh()}catch(e){showMsg(e.message)}};
$("saveCreatorPermission").onclick=async()=>{
 const b=$("saveCreatorPermission"),out=$("permissionMessage");
 const data={
  broadcaster_id:$("permissionBroadcasterId").value.trim(),
  broadcaster_name:$("permissionBroadcasterName").value.trim(),
  creator_permission_evidence:$("permissionCreatorEvidence").value.trim(),
  audio_rights_evidence:$("permissionAudioEvidence").value.trim(),
  confirm_audio_rights:$("permissionAudioConfirm").checked,
  max_source_seconds:Number($("permissionMaxSeconds").value),
  permission_expires_at:$("permissionExpiry").value?new Date($("permissionExpiry").value).toISOString():"",
  game_rights_basis:$("permissionGameBasis").value,
  game_rights_evidence_reference:$("permissionGameEvidence").value.trim(),
  noncommercial_use:$("permissionNoncommercial").checked,
  notes:$("permissionNotes").value.trim(),
  confirm_authorization:$("permissionConfirm").checked
 };
 b.disabled=true;b.textContent="KAYDEDİLİYOR...";
 try{await api("/api/permissions/grant",data);out.textContent="İzin kaydı onaylandı. Bu yayıncının klipleri yalnızca kayıtlı süre ve hak kapsamı içinde üretilebilir.";out.classList.remove("hidden");$("permissionConfirm").checked=false;$("permissionAudioConfirm").checked=false;await loadPermissions();await refresh();}
 catch(e){out.textContent=e.message;out.classList.remove("hidden");}
 finally{b.disabled=false;b.textContent="İZİN KAYDINI ONAYLA";}
};
$("permissionRows").addEventListener("click",async e=>{
 const b=e.target.closest("button[data-revoke-permission]");if(!b)return;
 const id=b.getAttribute("data-revoke-permission");
 if(!confirm("Bu yayıncının gelecekteki otomatik kullanımı durdurulsun mu?"))return;
 try{await api("/api/permissions/revoke",{broadcaster_id:id});await loadPermissions();}
 catch(err){$("permissionMessage").textContent=err.message;$("permissionMessage").classList.remove("hidden");}
});
loginCheck();
</script></body></html>`;

const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}});
const uid=()=>crypto.randomUUID();
async function ensureColumn(db,table,column,definition){const info=await db.prepare("PRAGMA table_info("+table+")").all();if(!(info.results||[]).some(x=>x.name===column))await db.prepare("ALTER TABLE "+table+" ADD COLUMN "+column+" "+definition).run();}
async function ensureTwitchSchema(db){
 await db.prepare(`CREATE TABLE IF NOT EXISTS twitch_oauth (id INTEGER PRIMARY KEY CHECK(id=1),user_id TEXT NOT NULL,login TEXT,display_name TEXT,access_token TEXT NOT NULL,refresh_token TEXT NOT NULL,scopes TEXT NOT NULL DEFAULT '[]',expires_at INTEGER,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 await db.prepare(`CREATE TABLE IF NOT EXISTS twitch_oauth_states (state TEXT PRIMARY KEY,expires_at INTEGER NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 await db.prepare(`CREATE TABLE IF NOT EXISTS twitch_clip_access (source_id TEXT PRIMARY KEY,clip_id TEXT,broadcaster_id TEXT,broadcaster_name TEXT,access_status TEXT NOT NULL DEFAULT 'unresolved',reason TEXT,checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 await ensureColumn(db,"twitch_clip_access","download_url","TEXT");
 await db.prepare(`CREATE TABLE IF NOT EXISTS twitch_broadcaster_access (broadcaster_id TEXT PRIMARY KEY,broadcaster_name TEXT,access_status TEXT NOT NULL DEFAULT 'unknown',reason TEXT,checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 for(const [c,d] of [["twitch_clip_id","TEXT"],["twitch_broadcaster_id","TEXT"],["twitch_resolved_at","TEXT"],["twitch_game_id","TEXT"],["twitch_clip_duration","REAL"],["relevance_status","TEXT DEFAULT 'unknown'"]])await ensureColumn(db,"sources",c,d);
}
async function ensureSchema(db){
 await db.prepare(`CREATE TABLE IF NOT EXISTS clip_analysis (source_id TEXT PRIMARY KEY,score INTEGER NOT NULL,relevance_score INTEGER NOT NULL,hook_score INTEGER NOT NULL,format_score INTEGER NOT NULL,score_reason TEXT,analyzed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 for(const [c,d] of [["media_duration","REAL"],["media_quality_score","INTEGER"],["scene_change_count","INTEGER"],["mean_volume_db","REAL"],["source_width","INTEGER"],["source_height","INTEGER"],["source_fps","REAL"],["source_has_audio","INTEGER"],["silence_ratio","REAL"],["media_usable","INTEGER"],["media_analysis_json","TEXT"],["media_analyzed_at","TEXT"]])await ensureColumn(db,"clip_analysis",c,d);
 await db.prepare(`CREATE TABLE IF NOT EXISTS shorts_drafts (id TEXT PRIMARY KEY,source_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'draft',title TEXT,script TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 for(const [c,d] of [["status","TEXT DEFAULT 'draft'"],["title","TEXT"],["script","TEXT"],["created_at","TEXT"],["updated_at","TEXT"],["source_url","TEXT"],["creator_name","TEXT"]])await ensureColumn(db,"shorts_drafts",c,d);
 await db.prepare(`CREATE TABLE IF NOT EXISTS permission_requests (id TEXT PRIMARY KEY,source_id TEXT NOT NULL,contact_method TEXT NOT NULL DEFAULT 'manual',contact_address TEXT,request_message TEXT NOT NULL,request_status TEXT NOT NULL DEFAULT 'draft',response_notes TEXT,evidence_reference TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 await db.prepare(`CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY,source_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'queued_review',target_format TEXT,editorial_note TEXT,output_key TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 await ensureColumn(db,"jobs","batch_id","TEXT");
 await db.prepare(`CREATE TABLE IF NOT EXISTS render_batches (id TEXT PRIMARY KEY,status TEXT NOT NULL DEFAULT 'active',target_min INTEGER NOT NULL DEFAULT 5,target_max INTEGER NOT NULL DEFAULT 10,max_attempts INTEGER NOT NULL DEFAULT 50,attempts INTEGER NOT NULL DEFAULT 0,pending INTEGER NOT NULL DEFAULT 0,published INTEGER NOT NULL DEFAULT 0,failed INTEGER NOT NULL DEFAULT 0,eligible INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)`).run();
 await ensureColumn(db,"render_batches","discovery_refreshed_at","TEXT");
 await ensureColumn(db,"render_batches","discovery_refresh_status","TEXT");
 await ensureColumn(db,"jobs","youtube_url","TEXT");
 await ensureColumn(db,"jobs","youtube_status","TEXT DEFAULT 'not_configured'");
 await ensureColumn(db,"jobs","render_attempts","INTEGER NOT NULL DEFAULT 0");
 await ensureColumn(db,"jobs","last_error","TEXT");
 await ensureColumn(db,"jobs","dispatch_started_at","TEXT");
 await ensureColumn(db,"jobs","package_url","TEXT");
 await ensureColumn(db,"jobs","thumbnail_status","TEXT DEFAULT 'not_available'");
 await db.prepare(`CREATE TABLE IF NOT EXISTS creator_usage_permissions (
  broadcaster_id TEXT PRIMARY KEY,
  broadcaster_name TEXT NOT NULL,
  permission_status TEXT NOT NULL DEFAULT 'pending',
  creator_permission_evidence TEXT NOT NULL,
  max_source_seconds REAL NOT NULL,
  permission_expires_at TEXT,
  game_rights_basis TEXT NOT NULL,
  game_rights_evidence_reference TEXT,
  audio_rights_evidence TEXT,
  audio_rights_confirmed INTEGER NOT NULL DEFAULT 0,
  noncommercial_use INTEGER NOT NULL DEFAULT 0,
  youtube_allowed INTEGER NOT NULL DEFAULT 1,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
 )`).run();
 await ensureColumn(db,"creator_usage_permissions","audio_rights_evidence","TEXT");
 await ensureColumn(db,"creator_usage_permissions","audio_rights_confirmed","INTEGER NOT NULL DEFAULT 0");
 await ensureColumn(db,"sources","twitch_broadcaster_id","TEXT");

}
function cookieValue(request){const list=(request.headers.get("Cookie")||"").split(";"),found=list.find(x=>x.trim().startsWith("gta6_session="));return found?found.trim().slice(13):"";}
function b64url(bytes){let s="";for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");}
async function sign(value,secret){const key=await crypto.subtle.importKey("raw",new TextEncoder().encode(secret),{name:"HMAC",hash:"SHA-256"},false,["sign"]);return b64url(new Uint8Array(await crypto.subtle.sign("HMAC",key,new TextEncoder().encode(value))));}
async function makeSession(secret){const expiry=String(Date.now()+43200000);return expiry+"."+await sign(expiry,secret);}
async function authorized(request,env){if(!env.APP_PASSWORD)return false;const parts=cookieValue(request).split(".");if(parts.length!==2||Number(parts[0])<Date.now())return false;return(await sign(parts[0],env.APP_PASSWORD))===parts[1];}
async function readBody(request){try{return await request.json()}catch{return {}}}
function isGta6Relevant(title){const t=String(title||"").toLowerCase();if(/\b(gta\s*v|gta\s*5|gta\s*online|grand theft auto v|grand theft auto online)\b/.test(t))return false;if(/\b(fortnite|counter[\s-]?strike|cs2|valorant|minecraft|roblox|apex legends|call of duty|warzone)\b/.test(t))return false;return /\b(gta\s*6|gta\s*vi|grand theft auto vi|grand theft auto 6)\b/.test(t);}
function scoreClip(title,views,duration){
 const t=String(title||"").toLowerCase(),v=Math.max(0,Number(views)||0),d=Math.max(0,Number(duration)||0);
 const strong=["insane","unbelievable","unexpected","shocking","wild","crazy","hilarious","funniest","funny","fails","fail","crash","collision","police","wanted","chase","arrest","fight","shootout","explosion","heist","robbery","secret","hidden","easter egg","rare","first","reaction","streamer reaction","npc","glitch","bug","physics","ragdoll","road rage","race","racing","drift","vehicle","car meet","new feature","update","discovery","strange","weird","ambush","escape","surprise","relationship","dating","girlfriend","boyfriend","romance","strip club","stripper","nightclub","club","bikini","swimsuit","underwear","hot tub","dance","dancing","adult","spicy","suggestive"];
 const mundane=["just running","running around","walking around","random driving","driving around","nothing happens","testing graphics"];
 const hookCount=strong.reduce((n,w)=>n+(t.includes(w)?1:0),0),mundanePenalty=mundane.some(w=>t.includes(w))?28:0;
 const relevance=25,hook=Math.min(40,hookCount*12),viewScore=v>=100000?20:v>=25000?16:v>=10000?12:v>=3000?8:v>=1000?4:0;
 const format=d>=45?22:0;
 const score=Math.max(0,Math.min(100,relevance+hook+viewScore+format-mundanePenalty));
 return{score,relevance_score:relevance,hook_score:hook,format_score:Math.min(25,format+viewScore),score_reason:"GTA VI category, standout event/mature-scene signals, view traction, Shorts duration and low-value-content penalty."};
}
async function analyzeSource(db,source,views=0,duration=30){const s=scoreClip(source.title,views,duration);await db.prepare(`INSERT INTO clip_analysis(source_id,score,relevance_score,hook_score,format_score,score_reason,analyzed_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(source_id) DO UPDATE SET score=CASE WHEN media_quality_score IS NOT NULL THEN ROUND(excluded.score*0.8+media_quality_score*0.2) ELSE excluded.score END,relevance_score=excluded.relevance_score,hook_score=excluded.hook_score,format_score=excluded.format_score,score_reason=excluded.score_reason,analyzed_at=CURRENT_TIMESTAMP`).bind(source.id,s.score,s.relevance_score,s.hook_score,s.format_score,s.score_reason).run();}
async function deriveTokenKey(env){const material=String(env.APP_PASSWORD||"")+"|"+String(env.TWITCH_CLIENT_SECRET||"")+"|gta6-twitch-token-v1",digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(material));return crypto.subtle.importKey("raw",digest,{name:"AES-GCM"},false,["encrypt","decrypt"]);}
function bytesToB64(bytes){let s="";for(const b of bytes)s+=String.fromCharCode(b);return btoa(s);}
function b64ToBytes(s){const raw=atob(s),out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out;}
async function encryptSecret(value,env){const iv=crypto.getRandomValues(new Uint8Array(12)),key=await deriveTokenKey(env),cipher=await crypto.subtle.encrypt({name:"AES-GCM",iv},key,new TextEncoder().encode(String(value)));return bytesToB64(iv)+"."+bytesToB64(new Uint8Array(cipher));}
async function decryptSecret(value,env){const[iv,cipher]=String(value||"").split(".");if(!iv||!cipher)throw new Error("Şifreli Twitch token verisi bozuk.");const key=await deriveTokenKey(env),plain=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64ToBytes(iv)},key,b64ToBytes(cipher));return new TextDecoder().decode(plain);}
function twitchRedirectUri(request){return new URL("/auth/twitch/callback",request.url).toString();}
async function createTwitchOAuthUrl(request,env){const state=uid();await env.DB.prepare("INSERT INTO twitch_oauth_states(state,expires_at) VALUES(?,?)").bind(state,Date.now()+600000).run();const params=new URLSearchParams({client_id:env.TWITCH_CLIENT_ID,redirect_uri:twitchRedirectUri(request),response_type:"code",scope:"editor:manage:clips channel:manage:clips",state});return"https://id.twitch.tv/oauth2/authorize?"+params.toString();}
async function exchangeTwitchCode(code,request,env){const response=await fetch("https://id.twitch.tv/oauth2/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({client_id:env.TWITCH_CLIENT_ID,client_secret:env.TWITCH_CLIENT_SECRET,code,grant_type:"authorization_code",redirect_uri:twitchRedirectUri(request)})}),data=await response.json();if(!response.ok||!data.access_token||!data.refresh_token)throw new Error("Twitch OAuth token alınamadı: "+(data.message||data.error||response.status));return data;}
async function twitchValidate(accessToken){const response=await fetch("https://id.twitch.tv/oauth2/validate",{headers:{Authorization:"OAuth "+accessToken}}),data=await response.json();if(!response.ok||!data.user_id)throw new Error("Twitch token doğrulanamadı.");return data;}
async function twitchUser(accessToken,env){const data=await twitchGet("https://api.twitch.tv/helix/users",env,accessToken);return data[0]||null;}
async function saveTwitchOAuth(env,tokenData,profile){await env.DB.prepare(`INSERT INTO twitch_oauth(id,user_id,login,display_name,access_token,refresh_token,scopes,expires_at,updated_at) VALUES(1,?,?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(id) DO UPDATE SET user_id=excluded.user_id,login=excluded.login,display_name=excluded.display_name,access_token=excluded.access_token,refresh_token=excluded.refresh_token,scopes=excluded.scopes,expires_at=excluded.expires_at,updated_at=CURRENT_TIMESTAMP`).bind(profile.id,profile.login||"",profile.display_name||profile.login||"",await encryptSecret(tokenData.access_token,env),await encryptSecret(tokenData.refresh_token,env),JSON.stringify(tokenData.scope||[]),Date.now()+Number(tokenData.expires_in||0)*1000).run();}
async function getTwitchOAuth(db,env){const row=await db.prepare("SELECT * FROM twitch_oauth WHERE id=1").first();if(!row)return null;return{...row,access_token:await decryptSecret(row.access_token,env),refresh_token:await decryptSecret(row.refresh_token,env),scopes:JSON.parse(row.scopes||"[]")};}
async function refreshTwitchOAuth(db,env,row){const response=await fetch("https://id.twitch.tv/oauth2/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({client_id:env.TWITCH_CLIENT_ID,client_secret:env.TWITCH_CLIENT_SECRET,grant_type:"refresh_token",refresh_token:row.refresh_token})}),data=await response.json();if(!response.ok||!data.access_token||!data.refresh_token)throw new Error("Twitch refresh token geçersiz. Twitch bağlantısını yeniden kur.");const profile=await twitchUser(data.access_token,env);if(!profile)throw new Error("Twitch kullanıcı bilgisi alınamadı.");await saveTwitchOAuth(env,data,profile);return await getTwitchOAuth(db,env);}
async function userTwitchToken(db,env){const row=await getTwitchOAuth(db,env);if(!row)return null;try{await twitchValidate(row.access_token);return row}catch(e){return await refreshTwitchOAuth(db,env,row);}}
function extractClipSlug(sourceUrl){try{const u=new URL(sourceUrl),host=u.hostname.toLowerCase().replace(/^www\./,"");if(host==="clips.twitch.tv")return u.pathname.split("/").filter(Boolean)[0]||null;if(host!=="twitch.tv")return null;const parts=u.pathname.split("/").filter(Boolean),i=parts.findIndex(x=>x.toLowerCase()==="clip");return i>=0&&parts[i+1]&&!parts[i+2]?parts[i+1]:null}catch{return null}}
async function countUnresolved(db){const r=await db.prepare("SELECT COUNT(*) AS n FROM sources WHERE platform='twitch' AND (twitch_clip_id IS NULL OR twitch_broadcaster_id IS NULL)").first();return Number(r?.n||0);}
async function accessCounts(db){const r=await db.prepare("SELECT access_status,COUNT(*) AS n FROM twitch_clip_access GROUP BY access_status").all(),out={downloadable:0,unauthorized:0,not_available:0,error:0,resolved:0,unresolved:0};for(const x of(r.results||[]))if(Object.prototype.hasOwnProperty.call(out,x.access_status))out[x.access_status]+=Number(x.n||0);return out;}
async function getDownloadStatus(db){const r=await db.prepare(`SELECT a.source_id,a.clip_id,a.broadcaster_id,a.broadcaster_name,a.access_status,CASE WHEN a.download_url IS NOT NULL AND a.download_url<>'' THEN 1 ELSE 0 END AS has_download_url,a.reason,a.checked_at,s.title,s.creator_name,s.source_url FROM twitch_clip_access a LEFT JOIN sources s ON s.id=a.source_id ORDER BY a.checked_at DESC LIMIT 500`).all();return{items:r.results||[]};}
async function validateResolvedClipDurations(db,env,limit=500){
 const safe=Math.max(1,Math.min(500,Number(limit)||500));
 const rows=(await db.prepare("SELECT id,twitch_clip_id FROM sources WHERE platform='twitch' AND twitch_clip_id IS NOT NULL AND (twitch_clip_duration IS NULL OR twitch_clip_duration<45) AND relevance_status='relevant' ORDER BY created_at ASC LIMIT ?").bind(safe).all()).results||[];
 if(!rows.length)return{checked:0,short:0,missing:0};
 const token=await twitchToken(env);let checked=0,short=0,missing=0;
 for(let i=0;i<rows.length;i+=100){
  const batch=rows.slice(i,i+100),q=batch.map(x=>"id="+encodeURIComponent(x.twitch_clip_id)).join("&");
  const clips=await twitchGet("https://api.twitch.tv/helix/clips?"+q,env,token),byId=new Map(clips.map(x=>[x.id,x]));
  for(const row of batch){
   const clip=byId.get(row.twitch_clip_id);
   if(!clip){missing++;await db.prepare("UPDATE sources SET relevance_status='irrelevant',twitch_clip_duration=0 WHERE id=?").bind(row.id).run();await db.prepare("UPDATE shorts_drafts SET status='blocked',updated_at=CURRENT_TIMESTAMP WHERE source_id=? AND status NOT IN ('processing','ready')").bind(row.id).run();await db.prepare("UPDATE jobs SET status='blocked',last_error='Twitch clip no longer exists; skipped.',updated_at=CURRENT_TIMESTAMP WHERE source_id=? AND status NOT IN ('processing','ready')").bind(row.id).run();continue;}
   const duration=Number(clip.duration||0);checked++;
   if(!Number.isFinite(duration)||duration<45){
    short++;await db.prepare("UPDATE sources SET twitch_clip_duration=?,relevance_status='irrelevant' WHERE id=?").bind(Number.isFinite(duration)?duration:0,row.id).run();
    await db.prepare("UPDATE shorts_drafts SET status='blocked',updated_at=CURRENT_TIMESTAMP WHERE source_id=? AND status NOT IN ('processing','ready')").bind(row.id).run();
    await db.prepare("UPDATE jobs SET status='blocked',last_error='Source clip is shorter than 45 seconds; skipped.',updated_at=CURRENT_TIMESTAMP WHERE source_id=? AND status NOT IN ('processing','ready')").bind(row.id).run();
    await db.prepare("UPDATE twitch_clip_access SET access_status='not_available',reason='Source clip is shorter than 45 seconds; skipped.',checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind(row.id).run();
   }else await db.prepare("UPDATE sources SET twitch_clip_duration=? WHERE id=?").bind(duration,row.id).run();
  }
 }
 return{checked,short,missing};
}
async function resolveTwitchClips(db,env,limit=20){const safe=Math.max(1,Math.min(500,Number(limit)||20)),rows=(await db.prepare(`SELECT id,source_url,creator_name,title FROM sources WHERE platform='twitch' AND (twitch_clip_id IS NULL OR twitch_broadcaster_id IS NULL) ORDER BY created_at ASC LIMIT ?`).bind(safe).all()).results||[];if(!rows.length){const result=await getDownloadStatus(db),c=await accessCounts(db);return{processed:0,resolved:0,downloadable:c.downloadable,unauthorized:c.unauthorized,errors:c.error,remaining:await countUnresolved(db),items:result.items};}
const appToken=await twitchToken(env),gta6GameId=await getGta6GameId(env,appToken);let resolved=0,errors=0,skipped=0;
for(const source of rows){const slug=extractClipSlug(source.source_url);if(!slug){skipped++;await db.prepare(`INSERT INTO twitch_clip_access(source_id,access_status,reason) VALUES(?,?,?) ON CONFLICT(source_id) DO UPDATE SET access_status=excluded.access_status,reason=excluded.reason,checked_at=CURRENT_TIMESTAMP`).bind(source.id,"not_available","Geçerli Twitch klip kimliği bulunamadı; kaynak atlandı.").run();continue;}
try{const data=await twitchGet("https://api.twitch.tv/helix/clips?id="+encodeURIComponent(slug),env,appToken),clip=data[0];if(!clip){skipped++;await db.prepare(`INSERT INTO twitch_clip_access(source_id,clip_id,access_status,reason) VALUES(?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET clip_id=excluded.clip_id,access_status=excluded.access_status,reason=excluded.reason,checked_at=CURRENT_TIMESTAMP`).bind(source.id,slug,"not_available","Twitch API klip kaydı döndürmedi; kaynak atlandı.").run();continue;}
const gameRows=(!gta6GameId&&clip.game_id)?await twitchGet("https://api.twitch.tv/helix/games?id="+encodeURIComponent(clip.game_id),env,appToken):[],gameName=String(gameRows[0]?.name||"").toLowerCase(),isGta6=!!gta6GameId?String(clip.game_id||"")===String(gta6GameId):(gameName==="grand theft auto vi"||gameName==="gta vi");
if(!isGta6){
 await db.prepare("UPDATE sources SET twitch_clip_id=?,twitch_broadcaster_id=?,twitch_game_id=?,relevance_status='irrelevant',twitch_resolved_at=CURRENT_TIMESTAMP WHERE id=?").bind(clip.id,clip.broadcaster_id,clip.game_id||null,source.id).run();
 await db.prepare("UPDATE shorts_drafts SET status='blocked',updated_at=CURRENT_TIMESTAMP WHERE source_id=? AND status NOT IN ('processing','ready')").bind(source.id).run();
 await db.prepare("UPDATE jobs SET status='blocked',editorial_note='Rejected: Twitch clip game category is not GTA VI.',updated_at=CURRENT_TIMESTAMP WHERE source_id=? AND status NOT IN ('processing','processing','ready')").bind(source.id).run();
 await db.prepare("INSERT INTO twitch_clip_access(source_id,clip_id,broadcaster_id,broadcaster_name,access_status,reason) VALUES(?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET clip_id=excluded.clip_id,broadcaster_id=excluded.broadcaster_id,broadcaster_name=excluded.broadcaster_name,access_status=excluded.access_status,reason=excluded.reason,checked_at=CURRENT_TIMESTAMP").bind(source.id,clip.id,clip.broadcaster_id,clip.broadcaster_name||source.creator_name||"Unknown","not_available","Klipin Twitch oyun kategorisi GTA VI değil: "+(gameName||clip.game_id||"bilinmiyor")).run();
 resolved++;continue;
}
await db.prepare("UPDATE sources SET twitch_clip_id=?,twitch_broadcaster_id=?,twitch_game_id=?,twitch_clip_duration=?,relevance_status='relevant',twitch_resolved_at=CURRENT_TIMESTAMP WHERE id=?").bind(clip.id,clip.broadcaster_id,clip.game_id||null,Number(clip.duration||0),source.id).run();
await db.prepare(`INSERT INTO twitch_clip_access(source_id,clip_id,broadcaster_id,broadcaster_name,access_status,reason) VALUES(?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET clip_id=excluded.clip_id,broadcaster_id=excluded.broadcaster_id,broadcaster_name=excluded.broadcaster_name,access_status=excluded.access_status,reason=excluded.reason,checked_at=CURRENT_TIMESTAMP`).bind(source.id,clip.id,clip.broadcaster_id,clip.broadcaster_name||source.creator_name||"Unknown","resolved","Klip bilgisi çözüldü.").run();resolved++;
}catch(e){errors++;await db.prepare(`INSERT INTO twitch_clip_access(source_id,access_status,reason) VALUES(?,?,?) ON CONFLICT(source_id) DO UPDATE SET access_status=excluded.access_status,reason=excluded.reason,checked_at=CURRENT_TIMESTAMP`).bind(source.id,"error",e.message).run();}}
const result=await getDownloadStatus(db),c=await accessCounts(db);return{processed:rows.length,resolved,skipped,downloadable:c.downloadable,unauthorized:c.unauthorized,errors,remaining:await countUnresolved(db),items:result.items};}
async function fetchClipDownloads(db,env,row,clipIds){const q=clipIds.map(id=>"clip_id="+encodeURIComponent(id)).join("&"),url="https://api.twitch.tv/helix/clips/downloads?editor_id="+encodeURIComponent(row.user_id)+"&broadcaster_id="+encodeURIComponent(row.broadcaster_id)+"&"+q;try{return await twitchGet(url,env,row.access_token)}catch(e){if(String(e.message).includes("401")){const fresh=await refreshTwitchOAuth(db,env,row),retryUrl="https://api.twitch.tv/helix/clips/downloads?editor_id="+encodeURIComponent(fresh.user_id)+"&broadcaster_id="+encodeURIComponent(row.broadcaster_id)+"&"+q;return await twitchGet(retryUrl,env,fresh.access_token)}throw e;}}
function isEditorPermissionError(error){const m=String(error?.message||error).toLowerCase();return m.includes("editor permissions")||m.includes("editor permission")||m.includes("not have editor")||m.includes("forbidden")||m.includes("unauthorized")||m.includes("403");}
async function markBroadcasterUnauthorized(db,broadcasterId,name,reason,rows){await db.prepare(`INSERT INTO twitch_broadcaster_access(broadcaster_id,broadcaster_name,access_status,reason,checked_at) VALUES(?,?,'unauthorized',?,CURRENT_TIMESTAMP) ON CONFLICT(broadcaster_id) DO UPDATE SET broadcaster_name=excluded.broadcaster_name,access_status='unauthorized',reason=excluded.reason,checked_at=CURRENT_TIMESTAMP`).bind(broadcasterId,name||"Unknown",reason).run();for(const x of rows)await db.prepare("UPDATE twitch_clip_access SET access_status='unauthorized',reason=?,checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind(reason,x.source_id).run();}
async function checkTwitchDownloads(db,env,limit=20){
 const resolved=await resolveTwitchClips(db,env,limit),connected=await userTwitchToken(db,env);
 if(!connected){const st=await getDownloadStatus(db);return{...resolved,items:st.items,skipped_broadcasters:0};}
 const all=(await db.prepare(`SELECT s.id AS source_id,s.twitch_clip_id AS clip_id,s.twitch_broadcaster_id AS broadcaster_id,COALESCE(s.creator_name,'Unknown') AS broadcaster_name,s.title,s.creator_name,s.source_url FROM sources s LEFT JOIN twitch_clip_access a ON a.source_id=s.id WHERE s.platform='twitch' AND s.twitch_clip_id IS NOT NULL AND s.twitch_broadcaster_id IS NOT NULL AND COALESCE(s.twitch_clip_duration,0)>=45 AND (a.source_id IS NULL OR (a.access_status IN ('resolved','error','unauthorized','not_available') AND datetime(COALESCE(a.checked_at,'1970-01-01'))<=datetime('now','-6 hours')) OR (a.access_status='downloadable' AND datetime(COALESCE(a.checked_at,'1970-01-01'))<=datetime('now','-20 minutes'))) ORDER BY COALESCE(a.checked_at,'1970-01-01') ASC LIMIT ?`).bind(Math.max(1,Math.min(500,Number(limit)||500))).all()).results||[];
 for(const x of all){await db.prepare(`INSERT INTO twitch_clip_access(source_id,clip_id,broadcaster_id,broadcaster_name,access_status,reason,download_url) VALUES(?,?,?,?,'resolved','Refreshing direct URL from Twitch Clips Downloads API.',NULL) ON CONFLICT(source_id) DO UPDATE SET clip_id=excluded.clip_id,broadcaster_id=excluded.broadcaster_id,broadcaster_name=excluded.broadcaster_name,access_status='resolved',reason=excluded.reason,download_url=NULL,checked_at=CURRENT_TIMESTAMP`).bind(x.source_id,x.clip_id,x.broadcaster_id,x.broadcaster_name).run();}
 const groups=new Map();for(const x of all){if(!groups.has(x.broadcaster_id))groups.set(x.broadcaster_id,[]);groups.get(x.broadcaster_id).push(x);}
 let apiErrors=0,downloadable=0,notAvailable=0,unauthorized=0;const errorDetails=[];
 for(const[broadcasterId,arr]of groups){for(let i=0;i<arr.length;i+=10){const batch=arr.slice(i,i+10);let data=null,batchError=null;
  try{data=await fetchClipDownloads(db,env,{...connected,broadcaster_id:broadcasterId},batch.map(x=>x.clip_id));}catch(e){batchError=e;}
  if(batchError){
   const batchMessage=String(batchError&&batchError.message||batchError).slice(0,500);
   // A 403 editor-permission response applies to this broadcaster, not to each clip separately.
   if(isEditorPermissionError(batchError)){
    await markBroadcasterUnauthorized(db,broadcasterId,batch[0]?.broadcaster_name,batchMessage,batch);
    unauthorized+=batch.length;
    errorDetails.push({broadcaster_id:broadcasterId,status:"unauthorized",count:batch.length,error:batchMessage});
    continue;
   }
   // Retry individually only for non-permission failures; one bad clip must not block its batch.
   for(const x of batch){try{const one=await fetchClipDownloads(db,env,{...connected,broadcaster_id:broadcasterId},[x.clip_id]);const d=(one||[]).find(v=>v.clip_id===x.clip_id),u=d&&(d.portrait_download_url||d.landscape_download_url);
    if(u){await db.prepare("UPDATE twitch_clip_access SET access_status='downloadable',download_url=?,reason=?,checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind(u,"Twitch Downloads API returned a direct MP4 URL.",x.source_id).run();downloadable++;}
    else{await db.prepare("UPDATE twitch_clip_access SET access_status='not_available',download_url=NULL,reason=?,checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind("Twitch Downloads API returned no download URL.",x.source_id).run();notAvailable++;}
   }catch(e){const msg=String(e&&e.message||e).slice(0,500),status=isEditorPermissionError(e)?"unauthorized":"error";if(status==="unauthorized")unauthorized++;else apiErrors++;await db.prepare("UPDATE twitch_clip_access SET access_status=?,download_url=NULL,reason=?,checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind(status,msg,x.source_id).run();errorDetails.push({source_id:x.source_id,status,error:msg});}}
   continue;
  }
  const found=new Map((data||[]).map(v=>[v.clip_id,v]));for(const x of batch){const d=found.get(x.clip_id),u=d&&(d.portrait_download_url||d.landscape_download_url);
   if(u){await db.prepare("UPDATE twitch_clip_access SET access_status='downloadable',download_url=?,reason=?,checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind(u,"Twitch Downloads API returned a direct MP4 URL.",x.source_id).run();downloadable++;}
   else{await db.prepare("UPDATE twitch_clip_access SET access_status='not_available',download_url=NULL,reason=?,checked_at=CURRENT_TIMESTAMP WHERE source_id=?").bind("Twitch Downloads API returned no download URL.",x.source_id).run();notAvailable++;}
  }
 }}
 const c=await accessCounts(db),st=await getDownloadStatus(db);
 return{processed:resolved.processed,resolved:resolved.resolved,downloadable:c.downloadable,unauthorized:c.unauthorized,not_available:c.not_available,errors:resolved.errors+apiErrors,error_details:errorDetails.slice(0,30),remaining:await countUnresolved(db),skipped_broadcasters:0,items:st.items};
}
async function twitchToken(env){if(!env.TWITCH_CLIENT_ID||!env.TWITCH_CLIENT_SECRET)throw new Error("Twitch API secrets eksik.");const response=await fetch("https://id.twitch.tv/oauth2/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({client_id:env.TWITCH_CLIENT_ID,client_secret:env.TWITCH_CLIENT_SECRET,grant_type:"client_credentials"})}),data=await response.json();if(!response.ok||!data.access_token)throw new Error("Twitch kimlik doğrulaması başarısız.");return data.access_token;}
async function twitchGet(url,env,token){const response=await fetch(url,{headers:{"Client-Id":env.TWITCH_CLIENT_ID,"Authorization":"Bearer "+token}}),data=await response.json();if(!response.ok)throw new Error("Twitch API: "+(data.message||response.status));return data.data||[];}
async function twitchGetPage(url,env,token){
 const response=await fetch(url,{headers:{"Client-Id":env.TWITCH_CLIENT_ID,"Authorization":"Bearer "+token}});
 const data=await response.json();
 if(!response.ok)throw new Error("Twitch API: "+(data.message||response.status));
 return{items:data.data||[],cursor:data.pagination?.cursor||null};
}
async function getGta6GameId(env,token){for(const name of["Grand Theft Auto VI","GTA VI"]){const games=await twitchGet("https://api.twitch.tv/helix/games?name="+encodeURIComponent(name),env,token),exact=games.find(g=>{const n=String(g.name||"").trim().toLowerCase();return n==="grand theft auto vi"||n==="gta vi"});if(exact)return exact.id;}return null;}
async function discover(db,env){const token=await twitchToken(env),gameId=await getGta6GameId(env,token);let clips=0,saved=0,duplicates=0,refreshed_existing=0,filtered=0,short_duration=0,wrong_category=0,channel_fallback_clips=0;const creators=new Map();
async function saveClip(clip,creatorFallback=null){clips++;const clipDuration=Number(clip.duration||0);if(!Number.isFinite(clipDuration)||clipDuration<45){filtered++;short_duration++;return;}const title=clip.title||"Untitled clip",gameRows=(!gameId&&clip.game_id)?await twitchGet("https://api.twitch.tv/helix/games?id="+encodeURIComponent(clip.game_id),env,token):[],categoryName=String(gameRows[0]?.name||"").toLowerCase(),categoryConfirmed=!!gameId?String(clip.game_id||"")===String(gameId):(categoryName==="grand theft auto vi"||categoryName==="gta vi");if(!categoryConfirmed){filtered++;wrong_category++;return;}const creatorName=clip.broadcaster_name||creatorFallback?.display_name||creatorFallback?.broadcaster_name||"Unknown";const exists=await db.prepare("SELECT id FROM sources WHERE twitch_clip_id=? OR source_url=? LIMIT 1").bind(clip.id,clip.url).first();if(exists){await db.prepare("UPDATE sources SET platform='twitch',source_url=?,creator_name=?,title=?,twitch_clip_id=?,twitch_broadcaster_id=?,twitch_game_id=?,twitch_clip_duration=?,relevance_status='relevant' WHERE id=?").bind(clip.url,creatorName,title,clip.id,clip.broadcaster_id||null,gameId||clip.game_id||null,clipDuration,exists.id).run();await analyzeSource(db,{id:exists.id,title},clip.view_count||0,clipDuration);duplicates++;refreshed_existing++;return;}const id=uid();if(clip.broadcaster_id)creators.set(clip.broadcaster_id,{id:clip.broadcaster_id,display_name:creatorName});await db.prepare(`INSERT INTO sources(id,platform,source_url,creator_name,title,rights_status,twitch_game_id,relevance_status,twitch_broadcaster_id,twitch_clip_id,twitch_clip_duration) VALUES(?,?,?,?,?,'pending',?,'relevant',?,?,?)`).bind(id,"twitch",clip.url,creatorName,title,gameId||clip.game_id||null,clip.broadcaster_id||null,clip.id,clipDuration).run();await analyzeSource(db,{id,title},clip.view_count||0,clipDuration);saved++;}
if(gameId){
 let cursor=null,pages=0;
 // Continue through all available recent GTA VI clip pages (up to 2,000).
 while(pages<20){
  const pageUrl="https://api.twitch.tv/helix/clips?game_id="+encodeURIComponent(gameId)+"&first=100"+(cursor?"&after="+encodeURIComponent(cursor):"");
  const page=await twitchGetPage(pageUrl,env,token);
  for(const clip of page.items)await saveClip(clip);
  pages++;
  cursor=page.cursor;
  if(!cursor)break;
 }
}
if(saved<5){
 // Broaden discovery to GTA VI channels when the game-category feed is too small.
 const queries=["GTA VI","GTA 6","Grand Theft Auto VI"],channels=new Map();
 for(const q of queries){const found=await twitchGet("https://api.twitch.tv/helix/search/channels?query="+encodeURIComponent(q)+"&first=30",env,token);for(const c of found)if(c.id)channels.set(c.id,c);}
 for(const creator of Array.from(channels.values()).slice(0,30)){
  const items=await twitchGet("https://api.twitch.tv/helix/clips?broadcaster_id="+encodeURIComponent(creator.id)+"&first=20",env,token);
  for(const clip of items){channel_fallback_clips++;await saveClip(clip,creator);}
 }
}
return{creators:creators.size,clips,saved,duplicates,refreshed_existing,filtered,short_duration,wrong_category,channel_fallback_clips,game_id:gameId||null};}
function makeEditorialPackage(source){const originalTitle=String(source.title||"GTA VI Moment").trim(),clean=originalTitle.replace(/\s+/g," ").slice(0,110),t=clean.toLowerCase();let angle="moment",hook="This GTA 6 moment deserves a closer look.",narration="The title points to an interesting GTA 6 moment. Watch the sequence closely, notice the details, and decide what stands out most to you.",captions=["A GTA 6 MOMENT WORTH WATCHING","LOOK CLOSELY","WHAT STOOD OUT TO YOU?"],question="What would you have noticed first?";
const rules=[{keys:["crash","car accident","collision","wreck","drift"],angle:"vehicle",hook:"One moment can change the whole drive in GTA 6.",narration:"This title points to a driving moment in GTA 6. Pay attention to the timing, the movement, and what happens around the vehicle. Would you have handled it differently?",captions:["GTA 6 DRIVING MOMENT","WATCH THE TIMING","HOW WOULD YOU REACT?"],question:"Would you have avoided it?"},{keys:["police","cop","wanted","arrest","chase"],angle:"police",hook:"A GTA 6 police moment you don't want to miss.",narration:"This clip title suggests a police encounter in GTA 6. Watch how the situation develops and look for the detail that changes the moment. What would your next move be?",captions:["GTA 6 POLICE MOMENT","WATCH WHAT HAPPENS","WHAT'S YOUR NEXT MOVE?"],question:"Would you run or stay?"},{keys:["funny","laugh","hilarious","fail","embarrassing"],angle:"comedy",hook:"GTA 6 moments like this are hard to predict.",narration:"The title frames this as a funny GTA 6 moment. The fun is in the timing, so watch the full sequence before deciding what makes it work. Which part got you?",captions:["GTA 6 FUNNY MOMENT","THE TIMING IS EVERYTHING","DID YOU LAUGH?"],question:"Which part was funniest?"},{keys:["secret","hidden","easter egg","mystery"],angle:"discovery",hook:"Could this be a detail worth looking for in GTA 6?",narration:"This title points toward a possible hidden detail or mystery. Take a close look at what the clip actually shows and decide whether it reveals something easy to miss.",captions:["GTA 6 DETAIL TO CHECK","LOOK CLOSER","DID YOU SPOT IT?"],question:"Did you notice it immediately?"},{keys:["explosion","explode","bomb","fire"],angle:"explosion",hook:"Keep your eyes on this GTA 6 moment.",narration:"The title suggests an explosive moment in GTA 6. Watch the full sequence and pay attention to the build-up and timing. What detail stood out to you?",captions:["GTA 6 ACTION MOMENT","WATCH THE BUILD-UP","WHAT STOOD OUT?"],question:"Did you expect that?"},{keys:["fight","punch","battle","combat","attack"],angle:"combat",hook:"A split-second decision can change a GTA 6 fight.",narration:"This title suggests a combat moment. Watch the positioning and timing, then decide what move made the biggest difference. What would you have done?",captions:["GTA 6 COMBAT MOMENT","WATCH THE TIMING","YOUR NEXT MOVE?"],question:"Which move would you choose?"},{keys:["graphic","detail","realistic","realism","physics"],angle:"detail",hook:"This is the kind of GTA 6 detail worth examining.",narration:"The title draws attention to a visual or gameplay detail. Look closely at the actual footage and decide what makes this moment interesting. Is this the kind of detail you want to see more often?",captions:["GTA 6 DETAIL CHECK","LOOK AT THE SMALL THINGS","DID YOU NOTICE?"],question:"Would you like more details like this?"},{keys:["mission","heist","robbery"],angle:"mission",hook:"Every decision matters in a GTA 6 mission.",narration:"This title points to a mission or heist-related moment. Follow the sequence and pay attention to the choices being made. What would your approach have been?",captions:["GTA 6 MISSION MOMENT","WATCH THE DECISIONS","WHAT'S YOUR PLAN?"],question:"How would you approach it?"},{keys:["character","lucia","jason"],angle:"character",hook:"Let's take a closer look at this GTA 6 character moment.",narration:"The title points to a character-focused moment in GTA 6. Pay attention to the presentation and the details visible in the clip. What stands out most to you?",captions:["GTA 6 CHARACTER MOMENT","WATCH THE DETAILS","WHO STOOD OUT?"],question:"Which character interests you most?"}];
rules.unshift({keys:["strip club","stripper","nightclub","bikini","swimsuit","underwear","hot tub","pole dance","adult scene","spicy","suggestive","seductive"],angle:"mature",hook:"GTA 6 is not holding back on its mature side. 👀",narration:"This clip highlights GTA 6's adult nightlife or suggestive content. Focus on what is actually visible and keep the commentary factual. How far do you think Rockstar should take the game's mature world?",captions:["GTA 6 AFTER DARK 👀","ROCKSTAR'S MATURE SIDE","TOO MUCH OR JUST GTA?"],question:"Should GTA 6 keep its mature edge?"},{keys:["relationship","dating","girlfriend","boyfriend","romance","couple"],angle:"relationship",hook:"GTA 6 could take player relationships to a whole new level.",narration:"This clip raises questions about relationships and character interactions in GTA 6. What does this suggest about player choice, and would you want a system like this in the game?",captions:["GTA 6 RELATIONSHIPS?","ROCKSTAR COULD GO THIS FAR?","WOULD YOU WANT THIS?"],question:"Should GTA 6 include deeper relationship systems?"});for(const rule of rules){if(rule.keys.some(k=>t.includes(k))){angle=rule.angle;hook=rule.hook;narration=rule.narration;captions=rule.captions;question=rule.question;break;}}
const englishTitles={mature:"GTA 6 AFTER DARK… ROCKSTAR WENT THERE?! 👀",relationship:"GTA 6 COULD CHANGE RELATIONSHIPS?! 😳",vehicle:"UNREAL GTA 6 DRIVING MOMENT! 🚗",police:"GTA 6 POLICE CHASE GETS WILD! 🚔",comedy:"THE FUNNIEST GTA 6 MOMENT! 😂",discovery:"HIDDEN GTA 6 DETAIL YOU MISSED! 👀",explosion:"INSANE GTA 6 ACTION! 💥",combat:"EPIC GTA 6 FIGHT! 👊",detail:"INCREDIBLE GTA 6 DETAIL! 👀",mission:"INTENSE GTA 6 MISSION MOMENT! 🎯",character:"GTA 6 CHARACTER MOMENT! 🔥",moment:"YOU HAVE TO SEE THIS GTA 6 MOMENT! 👀"};
const titleLeads={mature:"GTA 6 After Dark",relationship:"GTA 6 Relationships",vehicle:"GTA 6 Driving",police:"GTA 6 Police Chase",comedy:"GTA 6 Funny Moment",discovery:"GTA 6 Hidden Detail",explosion:"GTA 6 Action",combat:"GTA 6 Combat",detail:"GTA 6 Gameplay Detail",mission:"GTA 6 Mission",character:"GTA 6 Character",moment:"GTA 6 Gameplay"};
const topic=clean.replace(/\b(grand theft auto|gta)\s*(vi|6)?\b/gi," ").replace(/[|:!?]+/g," ").replace(/[^\p{L}\p{N}\s'-]/gu," ").replace(/\s+/g," ").trim();
const genericTopic=/^(gameplay|gta|gta vi|grand theft auto|highlight|clip|moment|gta gameplay|gta vi gameplay)$/i.test(topic);
const creator=String(source.creator_name||"").replace(/[^\p{L}\p{N} _-]/gu," ").replace(/\s+/g," ").trim().slice(0,24);
const variants={
 police:["A GTA 6 Police Chase That Escalates Fast | Shorts","This GTA 6 Escape Takes an Unexpected Turn | Shorts","A Split-Second GTA 6 Police Chase | Shorts"],
 vehicle:["A GTA 6 Driving Moment Gone Sideways | Shorts","This GTA 6 Road Moment Gets Intense | Shorts","One Wild Turn in This GTA 6 Drive | Shorts"],
 comedy:["An Unexpected GTA 6 Moment Caught on Stream | Shorts","This GTA 6 Moment Has Perfect Timing | Shorts","A Strange Turn in This GTA 6 Stream | Shorts"],
 discovery:["A GTA 6 Detail Worth a Closer Look | Shorts","Did You Notice This GTA 6 Detail? | Shorts","One More Detail to Check in GTA 6 | Shorts"],
 explosion:["A Sudden GTA 6 Action Moment | Shorts","This GTA 6 Scene Changes in Seconds | Shorts","A Huge Turn in This GTA 6 Moment | Shorts"],
 combat:["A GTA 6 Fight That Turns Quickly | Shorts","One Split-Second in This GTA 6 Fight | Shorts","A Tense GTA 6 Combat Moment | Shorts"],
 mission:["A GTA 6 Mission Moment to Watch | Shorts","One Choice Changes This GTA 6 Mission | Shorts","A Turn You Might Miss in GTA 6 | Shorts"],
 character:["A GTA 6 Character Moment to Notice | Shorts","A Closer Look at This GTA 6 Scene | Shorts","One Character Detail in GTA 6 | Shorts"],
 mature:["A GTA 6 Nightlife Moment Explained | Shorts","A Closer Look at GTA 6 After Dark | Shorts","GTA 6 Nightlife: What Stands Out? | Shorts"],
 relationship:["A GTA 6 Character Interaction to Notice | Shorts","A Closer Look at GTA 6 Relationships | Shorts","What This GTA 6 Interaction Shows | Shorts"],
 detail:["A GTA 6 Gameplay Detail Worth Seeing | Shorts","A Closer Look at This GTA 6 Moment | Shorts","One Small GTA 6 Detail to Notice | Shorts"],
 moment:["A GTA 6 Stream Moment Worth a Second Look | Shorts","An Unexpected Moment in This GTA 6 Clip | Shorts","A GTA 6 Moment That Changes Quickly | Shorts"]
};
const seedText=String(source.id||source.source_url||originalTitle),seed=Array.from(seedText).reduce((n,ch)=>(n*31+ch.charCodeAt(0))>>>0,7);
let title;
if(topic.length>=5&&!genericTopic){
 const base=(titleLeads[angle]||"GTA 6 Gameplay")+": "+topic;
 title=(base.length<39?base+" | GTA 6 Shorts":base).slice(0,60).replace(/[ ,:;|—-]+$/,"").trim();
}else if(creator){
 const creatorTail=["Worth a Second Look","One Detail to Notice","A Sudden Turn","Watch What Changes"];
 title=("GTA 6: "+creator.slice(0,16)+" — "+creatorTail[seed%creatorTail.length]+" | Shorts").slice(0,60);
}else{
 title=(variants[angle]||variants.moment)[seed%(variants[angle]||variants.moment).length];
}
if(title.length<40)title=(title+" | GTA 6 Shorts").slice(0,60);
const captionText=captions.join("\n"),script="SHORTS EDITORIAL PRODUCTION PACKAGE · 3.7\n\nSOURCE: "+(source.source_url||"")+"\nCREATOR: "+(source.creator_name||"Unknown")+"\nORIGINAL CLIP TITLE: "+originalTitle+"\nEDITORIAL ANGLE: "+angle+"\n\nPROPOSED TITLE:\n"+title+"\n\nHOOK / OPENING:\n"+hook+"\n\nVOICEOVER: DISABLED\nNo generated narration is added; source audio is retained only when the recorded usage permission covers it.\n\nCAPTIONS: DISABLED\nNo second subtitle layer is generated.\n\nENDING QUESTION:\n"+question+"\n\n9:16 EDITING PLAN:\n1. Use a sharp early gameplay frame for a 0.30-second branded opening.\n2. Start the selected gameplay immediately after the short cover transition.\n3. Keep the main gameplay subject inside the central safe area.\n4. Do not make factual claims that are not supported by the clip itself.\n5. Use only creator-authorized footage and stay within the recorded source-use time limit.\n6. Remove dead time without changing the meaning of the clip.\n7. Keep the final frame clean and readable.\n\nEDITORIAL NOTE:\nThis draft uses source-title signals only. The rendered footage is separately checked for face-cam overlays, blur and duplicate visual content.\n\nPRODUCTION STATUS:\nThis package can enter rendering only after creator permission and game-footage rights are recorded.";return{title,script};}
function extractNarration(script){const m=String(script||"").match(/ORIGINAL VOICEOVER DRAFT:\s*([\s\S]*?)\n\nCAPTION TEXT DRAFT:/);return m?m[1].trim():"";}
function buildYouTubeTags(sourceTitle,creatorName,angle){
 const base=["GTA 6","GTA VI","Grand Theft Auto VI","GTA 6 gameplay","GTA 6 clips","GTA 6 moments","GTA 6 shorts","gaming shorts","Vice City","Leonida","Rockstar Games"];
 const byAngle={
  police:["GTA 6 police chase","GTA 6 cops","GTA 6 wanted level"],
  vehicle:["GTA 6 cars","GTA 6 driving","GTA 6 crash"],
  comedy:["GTA 6 funny moments","GTA 6 fails"],
  discovery:["GTA 6 secrets","GTA 6 hidden details","GTA 6 easter eggs"],
  explosion:["GTA 6 explosions","GTA 6 action"],
  combat:["GTA 6 fights","GTA 6 combat"],
  detail:["GTA 6 graphics","GTA 6 details"],
  mission:["GTA 6 missions","GTA 6 heists"],
  character:["GTA 6 characters"],
  mature:["GTA 6 nightlife"],
  relationship:["GTA 6 relationships"]
 };
 const topic=String(sourceTitle||"").replace(/\b(grand theft auto|gta)\s*(vi|6)?\b/gi," ").replace(/[^\p{L}\p{N} ]/gu," ").trim();
const words=topic.toLowerCase().split(/\s+/).filter(w=>w.length>=3&&!["the","and","with","this","that","from","into","just","clip","gta","grand","theft","auto"].includes(w));
 const derived=[];
 for(let i=0;i<words.length&&derived.length<5;i++)derived.push("GTA 6 "+words[i]);
 if(words.length>=2)derived.push("GTA 6 "+words.slice(0,2).join(" "));
 const creator=String(creatorName||"").trim().replace(/[^a-zA-Z0-9 _-]/g," ").replace(/\s+/g," ").slice(0,35);
 const candidates=[...base,...(byAngle[angle]||[]),...derived,...(topic.length>=5&&topic.length<=55?[topic]:[]),...(creator?[creator,creator+" Twitch"]:[])];
 const result=[];let total=0;
 for(const raw of candidates){
  const tag=String(raw||"").trim().replace(/\s+/g," ");
  if(!tag||result.some(x=>x.toLowerCase()===tag.toLowerCase())||result.length>=25)continue;
  if(total+tag.length+1>480)continue;
  result.push(tag);total+=tag.length+1;
 }
 return result;
}
async function dispatchRender(db,env,draftId,evidenceReference,authorizationConfirmation,batchId=null){
 if(!env.GITHUB_TOKEN)return {error:"Cloudflare Worker'da GITHUB_TOKEN secret eksik. GitHub Actions workflow_dispatch yetkili token eklenmeli."};
 if(!env.RENDER_WEBHOOK_SECRET)return {error:"Render izin imzası için RENDER_WEBHOOK_SECRET eksik; güvenli render durduruldu."};
 const row=await db.prepare(`SELECT d.id AS draft_id,d.source_id,d.title AS draft_title,d.script,d.status AS draft_status,s.source_url,s.title AS source_title,s.creator_name,s.rights_status,s.relevance_status,s.twitch_game_id,s.twitch_broadcaster_id,s.twitch_clip_duration,p.broadcaster_id AS permission_broadcaster_id,p.max_source_seconds,p.permission_expires_at,p.game_rights_basis,p.noncommercial_use,j.id AS job_id,j.status AS job_status,j.output_key,j.last_error,j.render_attempts FROM shorts_drafts d JOIN sources s ON s.id=d.source_id LEFT JOIN creator_usage_permissions p ON p.broadcaster_id=s.twitch_broadcaster_id AND p.permission_status='approved' AND p.youtube_allowed=1 AND p.audio_rights_confirmed=1 AND trim(coalesce(p.audio_rights_evidence,''))<>'' AND trim(coalesce(p.creator_permission_evidence,''))<>'' AND p.max_source_seconds>=45 AND ((p.game_rights_basis='publisher_written_permission' AND trim(coalesce(p.game_rights_evidence_reference,''))<>'') OR (p.game_rights_basis='rockstar_noncommercial_guidelines' AND p.noncommercial_use=1)) AND (p.permission_expires_at IS NULL OR datetime(p.permission_expires_at)>datetime('now')) LEFT JOIN jobs j ON j.source_id=s.id WHERE d.id=? ORDER BY j.created_at DESC LIMIT 1`).bind(draftId).first();
 if(!row)return {error:"Üretim paketi bulunamadı."};
 if(row.relevance_status!=="relevant"||!row.twitch_game_id)return {error:"Bu kaynak Twitch üzerinde GTA VI kategorisinde doğrulanmadı. Yalnızca GTA VI klipleri üretilebilir."};
 if(!row.permission_broadcaster_id)return {error:"Bu yayıncı için geçerli YouTube kullanım izni ve GTA VI görüntüsü hak dayanağı kaydı yok; yayın engellendi."};
 if(!extractClipSlug(String(row.source_url||"")))return {error:"Yalnızca gerçek Twitch klip bağlantıları işlenebilir."};
 if(!row.job_id)return {error:"Bu paket için üretim işi kaydı bulunamadı. Önce paketleri güncelle."};
 if(["processing","ready"].includes(row.job_status))return {ok:true,already_exists:true,job_id:row.job_id,status:row.job_status,output_key:row.output_key||null,last_error:row.last_error||null,message:row.job_status==="ready"?"Bu klibin MP4 üretimi tamamlanmış. İndirme bağlantısı hazır.":"Bu klip zaten render kuyruğunda. İşlem tamamlanınca indirme bağlantısı görünecek."};
 if(Number(row.render_attempts||0)>=10)return {error:"Bu iş için 10 render denemesi tamamlandı. Otomatik tekrar durduruldu."};
 // User-triggered render; no evidence URL prompt and no automatic rights-record mutation.

 const title=String(row.draft_title||row.source_title||"GTA 6 Short").slice(0,90);
 const maxSourceSeconds=Math.max(45,Math.min(175,Number(row.max_source_seconds)||45));
 const nextRenderAttempt=String(Number(row.render_attempts||0)+1);
 const downloadAccess=await db.prepare("SELECT download_url FROM twitch_clip_access WHERE source_id=? AND access_status='downloadable' AND download_url IS NOT NULL AND datetime(checked_at)>datetime('now','-30 minutes')").bind(row.source_id).first();
 if(!downloadAccess?.download_url)return{error:"Twitch Downloads API tarafından son 30 dakika içinde verilmiş doğrudan indirme URL'si yok; güvenli render durduruldu."};
 const downloadUrl=String(downloadAccess.download_url);
 const permissionAttestationPayload=[row.job_id,row.source_url,row.twitch_broadcaster_id,String(maxSourceSeconds),row.permission_expires_at||"",nextRenderAttempt,downloadUrl].join("\n");
 const permissionAttestation=await sign(permissionAttestationPayload,env.RENDER_WEBHOOK_SECRET);
 const questionMatch=String(row.script||"").match(/ENDING QUESTION:\s*([^\n]+)/);
 const original=String(row.source_title||row.draft_title||"GTA 6 moment").replace(/\s+/g," ").trim().slice(0,180);
 const angleMatch=String(row.script||"").match(/EDITORIAL ANGLE:\s*([a-z_]+)/i);
 const angle=angleMatch?angleMatch[1].toLowerCase():"moment";
 const topic=original.replace(/\b(grand theft auto|gta)\s*(vi|6)?\b/gi," ").replace(/[^\p{L}\p{N}\s'-]/gu," ").replace(/[|:]+/g," ").replace(/\s+/g," ").trim();
const safeTopic=topic.length>=5?topic:"a GTA 6 gameplay moment";
 const angleHashtag=({police:"#GTA6Police",vehicle:"#GTA6Cars",comedy:"#GTA6Funny",discovery:"#GTA6Secrets",explosion:"#GTA6Action",combat:"#GTA6Combat",mission:"#GTA6Missions",character:"#GTA6Characters",detail:"#GTA6Graphics",mature:"#GTA6Nightlife",relationship:"#GTA6Story"})[angle]||"#GTA6Gameplay";
 const creatorCredit=String(row.creator_name||"Twitch creator").replace(/[^\p{L}\p{N} _-]/gu," ").replace(/\s+/g," ").trim().slice(0,80)||"Twitch creator";
 const description=[
  safeTopic+" in Grand Theft Auto VI (GTA 6).",
  "What stood out in this clip, and what would you do next?",
  "Subscribe to VI RUSH for more GTA VI clips and gameplay moments.",
  "Clip creator: "+creatorCredit+".",
  "Source: "+String(row.source_url||""),
  "#GTA6 #GTAVI "+angleHashtag+" #Shorts"
 ].join("\n\n").slice(0,5000);
 const tags=buildYouTubeTags(original,row.creator_name,angle);
 const claim=await db.prepare("UPDATE jobs SET status='processing',batch_id=?,render_attempts=COALESCE(render_attempts,0)+1,last_error=NULL,dispatch_started_at=CURRENT_TIMESTAMP,editorial_note='Authorized render dispatched to GitHub Actions.',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('queued_review','failed')").bind(batchId,row.job_id).run();
 if(Number(claim?.meta?.changes||0)===0){
  const current=await db.prepare("SELECT status FROM jobs WHERE id=?").bind(row.job_id).first();
  if(["processing","ready"].includes(current?.status))return{ok:true,already_exists:true,job_id:row.job_id,status:current.status};
  return{error:"Üretim işi başka bir işlem tarafından değiştirildi; bu deneme güvenli şekilde atlandı."};
 }
 await db.prepare("UPDATE shorts_drafts SET status='processing',updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(row.draft_id).run();
 let response;
 try{response=await fetch("https://api.github.com/repos/alperengkhn-sys/gta6-shorts-factory/actions/workflows/render-short.yml/dispatches",{method:"POST",headers:{"Authorization":"Bearer "+env.GITHUB_TOKEN,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json","User-Agent":"GTA6-Shorts-Factory"},body:JSON.stringify({ref:"main",inputs:{source_url:row.source_url,download_url:downloadUrl,title,description,creator_name:String(row.creator_name||"Unknown"),source_title:String(row.source_title||title),package_text:String(row.script||""),tags:JSON.stringify(tags),max_source_seconds:String(maxSourceSeconds),broadcaster_id:String(row.twitch_broadcaster_id),permission_expires_at:String(row.permission_expires_at||""),permission_attestation:permissionAttestation,job_id:row.job_id,render_attempt:nextRenderAttempt}})});}
 catch(error){const detail=String(error&&error.message||error).slice(0,1000);await db.prepare("UPDATE jobs SET status='failed',editorial_note=?,last_error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?").bind("GitHub dispatch network error: "+detail,detail,row.job_id).run();await db.prepare("UPDATE shorts_drafts SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(row.draft_id).run();return {error:"GitHub Actions bağlantı hatası: "+detail};}
 if(response.status!==204){
  const detail=(await response.text()).slice(0,1200);
  await db.prepare("UPDATE jobs SET status='failed',editorial_note=?,last_error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?").bind("GitHub workflow_dispatch failed: HTTP "+response.status+" "+detail,detail,row.job_id).run();
  await db.prepare("UPDATE shorts_drafts SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(row.draft_id).run();
  // A signed, short-lived Twitch CDN URL must never be written into the public render-queue directory.
  return {error:"GitHub Actions işi başlatılamadı (HTTP "+response.status+"). "+detail};
 }
 return {ok:true,job_id:row.job_id,status:"processing"};
}
async function renderCallback(request,env,db){
 if(!env.RENDER_WEBHOOK_SECRET||request.headers.get("X-Render-Secret")!==env.RENDER_WEBHOOK_SECRET)return json({error:"Webhook authentication failed."},401);
 const data=await readBody(request),jobId=String(data.job_id||"");
 if(!jobId)return json({error:"job_id required."},400);
 const job=await db.prepare("SELECT id,source_id,status,render_attempts,batch_id FROM jobs WHERE id=?").bind(jobId).first();
 if(!job)return json({error:"Job not found."},404);
 if(data.render_attempt!==undefined&&data.render_attempt!==null&&data.render_attempt!==""&&Number(data.render_attempt)!==Number(job.render_attempts))return json({error:"Stale render callback rejected."},409);
 if(job.status==="ready")return json({ok:true,status:"ready",duplicate:true});
 if(job.status!=="processing")return json({ok:true,status:job.status,duplicate:true});
 const renderOk=(data.render_conclusion||data.conclusion)==="success",youtubeStatus=String(data.youtube_status||"not_run").slice(0,40),thumbnailStatus=String(data.thumbnail_status||"not_available").slice(0,40),youtubeUrl=String(data.youtube_url||"").slice(0,1000),youtubeOk=youtubeStatus.startsWith("uploaded_")&&/^https:\/\/www\.youtube\.com\/watch\?v=[A-Za-z0-9_-]{11}$/.test(youtubeUrl),ok=renderOk&&youtubeOk,status=ok?"ready":"failed",output=String(data.artifact_url||data.run_url||"").slice(0,2000),packageUrl=String(data.package_url||"").slice(0,2000);
 const thumbnailNote=thumbnailStatus==="uploaded"?"Custom thumbnail uploaded.":"Custom thumbnail status: "+thumbnailStatus+".";
 const note=[ok?"Render and YouTube upload completed.":(renderOk?"Render completed but YouTube upload was not confirmed.":"Render failed."), "YouTube: "+youtubeStatus,thumbnailNote,data.error||""].filter(Boolean).join(" ").slice(0,1500);
 let mediaSaved=false;
 const m=data.media_analysis&&typeof data.media_analysis==="object"?data.media_analysis:null;
 if(ok&&m){
  const duration=Number(m.duration),width=Number(m.video?.width),height=Number(m.video?.height),fps=Number(m.video?.fps),silence=Number(m.silence_ratio);
  if(Number.isFinite(duration)&&duration>0&&duration<=3600&&Number.isFinite(width)&&width>0&&width<=16384&&Number.isFinite(height)&&height>0&&height<=16384&&Number.isFinite(fps)&&fps>=0&&fps<=240&&Number.isFinite(silence)&&silence>=0&&silence<=1){
   await db.prepare("INSERT INTO clip_analysis(source_id,score,relevance_score,hook_score,format_score,score_reason) VALUES(?,0,0,0,0,'Media analysis received from render') ON CONFLICT(source_id) DO NOTHING").bind(job.source_id).run();
   const resolutionScore=Math.min(100,(width*height)/(1920*1080)*100),fpsScore=Math.min(100,(fps/30)*100),audioScore=m.audio?.present?100:65,silenceScore=Math.max(0,100-silence*100);
   const mediaQuality=Math.round(resolutionScore*0.4+fpsScore*0.2+audioScore*0.25+silenceScore*0.15);
   const sceneChanges=Number.isInteger(m.scene_change_count)&&m.scene_change_count>=0?m.scene_change_count:null,meanVolume=m.mean_volume_db!==null&&m.mean_volume_db!==undefined&&Number.isFinite(Number(m.mean_volume_db))?Number(m.mean_volume_db):null;
   await db.prepare("UPDATE clip_analysis SET score=CASE WHEN media_analyzed_at IS NULL THEN ROUND(score*0.8+?*0.2) ELSE score END,media_quality_score=?,scene_change_count=?,mean_volume_db=?,media_duration=?,source_width=?,source_height=?,source_fps=?,source_has_audio=?,silence_ratio=?,media_usable=?,media_analysis_json=?,media_analyzed_at=COALESCE(media_analyzed_at,CURRENT_TIMESTAMP) WHERE source_id=?").bind(mediaQuality,mediaQuality,sceneChanges,meanVolume,duration,Math.round(width),Math.round(height),fps,m.audio?.present?1:0,silence,m.usable_for_shorts?1:0,JSON.stringify(m).slice(0,8000),job.source_id).run();
   mediaSaved=true;
  }
 }
 await db.prepare("UPDATE jobs SET status=?,output_key=?,package_url=?,youtube_url=?,youtube_status=?,thumbnail_status=?,editorial_note=?,last_error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(status,output,packageUrl,youtubeUrl,youtubeStatus,thumbnailStatus,note,ok?null:note,jobId).run();
 await db.prepare("UPDATE shorts_drafts SET status=?,updated_at=CURRENT_TIMESTAMP WHERE source_id=?").bind(status,job.source_id).run();
 let batch=null;
 if(job.batch_id){
  await db.prepare("UPDATE render_batches SET pending=MAX(0,pending-1),published=published+?,failed=failed+?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(ok?1:0,ok?0:1,job.batch_id).run();
  await fillRenderBatch(db,env,job.batch_id);
  batch=await db.prepare("SELECT id,status,target_min,target_max,attempts,pending,published,failed,eligible FROM render_batches WHERE id=?").bind(job.batch_id).first();
 }
 return json({ok:true,status,media_analysis_saved:mediaSaved,batch:batch||null});
}
async function prepareAll(db){const result=await db.prepare(`SELECT s.id,s.title,s.creator_name,s.source_url,s.rights_status,s.relevance_status,s.twitch_game_id,s.twitch_broadcaster_id,s.twitch_clip_duration,p.broadcaster_id AS permission_broadcaster_id,a.score FROM sources s LEFT JOIN clip_analysis a ON a.source_id=s.id LEFT JOIN creator_usage_permissions p ON p.broadcaster_id=s.twitch_broadcaster_id AND p.permission_status='approved' AND p.youtube_allowed=1 AND p.audio_rights_confirmed=1 AND trim(coalesce(p.audio_rights_evidence,''))<>'' AND p.max_source_seconds>=45 AND trim(coalesce(p.creator_permission_evidence,''))<>'' AND ((p.game_rights_basis='publisher_written_permission' AND trim(coalesce(p.game_rights_evidence_reference,''))<>'') OR (p.game_rights_basis='rockstar_noncommercial_guidelines' AND p.noncommercial_use=1)) AND (p.permission_expires_at IS NULL OR datetime(p.permission_expires_at)>datetime('now')) ORDER BY s.created_at ASC`).all(),rows=result.results||[];let created=0,updated=0,existing=0,skippedIrrelevant=0,skippedPermission=0;const statements=[];
for(const source of rows){if(source.relevance_status==="irrelevant"){skippedIrrelevant++;continue;}const categoryConfirmed=!!source.twitch_game_id&&source.relevance_status==="relevant";if(!categoryConfirmed){skippedIrrelevant++;continue;}if(!source.permission_broadcaster_id){skippedPermission++;continue;}const pack=makeEditorialPackage(source),found=await db.prepare("SELECT id,status FROM shorts_drafts WHERE source_id=? LIMIT 1").bind(source.id).first();if(found){existing++;await db.prepare("UPDATE shorts_drafts SET title=?,script=?,source_url=?,creator_name=?,updated_at=CURRENT_TIMESTAMP WHERE id=?").bind(pack.title,pack.script,source.source_url,source.creator_name||"Unknown",found.id).run();const existingJob=await db.prepare("SELECT id FROM jobs WHERE source_id=? LIMIT 1").bind(source.id).first();if(!existingJob)await db.prepare("INSERT INTO jobs(id,source_id,status,target_format,editorial_note,output_key) VALUES(?,?,'queued_review','shorts_9_16','Legacy draft migrated to cloud render queue.',NULL)").bind(uid(),source.id).run();updated++;continue;}const draftId=uid();statements.push(db.prepare(`INSERT INTO shorts_drafts(id,source_id,status,title,script,created_at,updated_at,source_url,creator_name) VALUES (?,?,'queued_review',?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,?,?)`).bind(draftId,source.id,pack.title,pack.script,source.source_url,source.creator_name||"Unknown"));statements.push(db.prepare(`INSERT INTO jobs(id,source_id,status,target_format,editorial_note,output_key) VALUES (?,?,'queued_review','shorts_9_16',?,NULL)`).bind(uid(),source.id,"Editorial package prepared. Automatic rendering accepts verified GTA VI Twitch clips of at least 45 seconds; exports are capped at 180 seconds including the intro."));created++;}
for(let i=0;i<statements.length;i+=40)await db.batch(statements.slice(i,i+40));const total=await db.prepare("SELECT COUNT(*) AS n FROM shorts_drafts WHERE status='queued_review'").first();return{checked:rows.length,created,updated,existing,skipped_irrelevant:skippedIrrelevant,skipped_permission:skippedPermission,total:Number(total?.n||0)};}
async function fillRenderBatch(db,env,batchId,discoveryAlreadyRefreshed=false){
 let attempted=0,dispatched=0,alreadyExisting=0,dispatchErrors=0;
 const errors=[];
 while(attempted<MAX_AUTOMATIC_ATTEMPTS_PER_CYCLE){
  const batch=await db.prepare("SELECT id,status,target_min,target_max,max_attempts,attempts,pending,published,failed,eligible FROM render_batches WHERE id=?").bind(batchId).first();
  if(!batch||batch.status!=="active")break;
  // One render at a time: save the visual fingerprint before the next source starts.
  if(Number(batch.pending)>=MAX_IN_FLIGHT_BATCH_RENDERS)break;
  if(!shouldFillBatch(batch)){
   if(Number(batch.pending)===0&&(Number(batch.published)>=Number(batch.target_max)||Number(batch.attempts)>=Number(batch.max_attempts))){
    await db.prepare("UPDATE render_batches SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(batchCompletionStatus(batch),batchId).run();
   }
   break;
  }
  const reservation=await db.prepare("UPDATE render_batches SET pending=pending+1,attempts=attempts+1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active' AND published+pending<target_max AND attempts<max_attempts AND pending<? RETURNING id").bind(batchId,MAX_IN_FLIGHT_BATCH_RENDERS).first();
  if(!reservation)break;
  const findCandidate=()=>db.prepare("SELECT DISTINCT d.id AS draft_id FROM shorts_drafts d JOIN sources s ON s.id=d.source_id JOIN creator_usage_permissions p ON p.broadcaster_id=s.twitch_broadcaster_id AND p.permission_status='approved' AND p.youtube_allowed=1 AND p.audio_rights_confirmed=1 AND trim(coalesce(p.audio_rights_evidence,''))<>'' AND trim(coalesce(p.creator_permission_evidence,''))<>'' AND p.max_source_seconds>=45 AND ((p.game_rights_basis='publisher_written_permission' AND trim(coalesce(p.game_rights_evidence_reference,''))<>'') OR (p.game_rights_basis='rockstar_noncommercial_guidelines' AND p.noncommercial_use=1)) AND (p.permission_expires_at IS NULL OR datetime(p.permission_expires_at)>datetime('now')) JOIN twitch_clip_access ta ON ta.source_id=s.id AND ta.access_status='downloadable' AND ta.download_url IS NOT NULL AND datetime(ta.checked_at)>datetime('now','-30 minutes') JOIN jobs j ON j.id=(SELECT j2.id FROM jobs j2 WHERE j2.source_id=s.id ORDER BY j2.created_at DESC LIMIT 1) LEFT JOIN clip_analysis a ON a.source_id=s.id WHERE s.platform='twitch' AND s.relevance_status='relevant' AND s.twitch_game_id IS NOT NULL AND s.twitch_clip_duration>=45 AND j.status IN ('queued_review','failed') AND COALESCE(j.render_attempts,0)<10 AND COALESCE(j.batch_id,'')<>? AND COALESCE(j.last_error,'') NOT LIKE '%Quality gate rejected%' AND COALESCE(j.last_error,'') NOT LIKE '%Offline quality rules rejected%' ORDER BY CASE WHEN j.status='queued_review' THEN 0 ELSE 1 END,COALESCE(a.score,0) DESC,j.created_at ASC LIMIT 1").bind(batchId).first();
  let candidate=await findCandidate();
  if(!candidate){
   // The caller may have completed discovery immediately before creating/filling this batch.
   // Avoid a second full Twitch scan in the same Worker invocation (subrequest quota).
   if(discoveryAlreadyRefreshed){
    let state=await db.prepare("SELECT discovery_refresh_status FROM render_batches WHERE id=?").bind(batchId).first();
    if(state?.discovery_refresh_status==="running"){
     for(let wait=0;wait<20&&!candidate;wait++){
      state=await db.prepare("SELECT discovery_refresh_status FROM render_batches WHERE id=?").bind(batchId).first();
      if(state?.discovery_refresh_status!=="running")break;
      await new Promise(resolve=>setTimeout(resolve,500));
      candidate=await findCandidate();
     }
    }else if(state?.discovery_refresh_status==null){
     await db.prepare("UPDATE render_batches SET discovery_refresh_status='complete',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active' AND discovery_refresh_status IS NULL").bind(batchId).run();
    }
   }else{
    // Expand the source pool only once per active batch when no earlier discovery pass ran.
    const scan=await db.prepare("UPDATE render_batches SET discovery_refreshed_at=CURRENT_TIMESTAMP,discovery_refresh_status='running',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active' AND discovery_refresh_status IS NULL RETURNING id").bind(batchId).first();
    if(scan){
     try{
      const discovery=await discover(db,env);
      const prepared=await prepareAll(db);
      errors.push({discovery_expansion:{clips:discovery?.clips||0,saved:discovery?.saved||0,prepared:prepared?.created||0}});
     }catch(error){
      errors.push({discovery_expansion_error:String(error&&error.message||error).slice(0,500)});
     }finally{
      await db.prepare("UPDATE render_batches SET discovery_refresh_status='complete',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(batchId).run();
     }
     candidate=await findCandidate();
    }else{
     // A sibling callback owns discovery. Briefly wait before releasing our reserved slot.
     for(let wait=0;wait<20&&!candidate;wait++){
      const state=await db.prepare("SELECT discovery_refresh_status FROM render_batches WHERE id=?").bind(batchId).first();
      if(state?.discovery_refresh_status!=="running")break;
      await new Promise(resolve=>setTimeout(resolve,500));
      candidate=await findCandidate();
     }
    }
   }
  }
  if(!candidate){
   await db.prepare("UPDATE render_batches SET pending=MAX(0,pending-1),updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(batchId).run();
   const afterEmpty=await db.prepare("SELECT id,status,target_min,target_max,max_attempts,attempts,pending,published,failed,eligible FROM render_batches WHERE id=?").bind(batchId).first();
   if(afterEmpty&&Number(afterEmpty.pending)===0)await db.prepare("UPDATE render_batches SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(batchCompletionStatus(afterEmpty),batchId).run();
   break;
  }
  attempted++;
  const result=await dispatchRender(db,env,candidate.draft_id,"",null,batchId);
  if(result.ok&&!result.already_exists){
   dispatched++;
   continue;
  }
  await db.prepare("UPDATE render_batches SET pending=MAX(0,pending-1),failed=failed+1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(batchId).run();
  if(result.already_exists)alreadyExisting++;
  else if(result.error){
   dispatchErrors++;
   errors.push({draft_id:candidate.draft_id,error:String(result.error).slice(0,500)});
  }
 }
 let finalBatch=await db.prepare("SELECT id,status,target_min,target_max,max_attempts,attempts,pending,published,failed,eligible FROM render_batches WHERE id=?").bind(batchId).first();
 if(finalBatch&&finalBatch.status==="active"&&Number(finalBatch.pending)===0&&(Number(finalBatch.published)>=Number(finalBatch.target_max)||Number(finalBatch.attempts)>=Number(finalBatch.max_attempts))){
  await db.prepare("UPDATE render_batches SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(batchCompletionStatus(finalBatch),batchId).run();
  finalBatch=await db.prepare("SELECT id,status,target_min,target_max,max_attempts,attempts,pending,published,failed,eligible FROM render_batches WHERE id=?").bind(batchId).first();
 }
 return{batch:finalBatch,attempted,dispatched,already_existing:alreadyExisting,dispatchErrors,errors};
}
async function dispatchQueuedRenders(db,env,limit=MAX_AUTOMATIC_RENDERS_PER_CYCLE,discoveryAlreadyRefreshed=false){
 if(!env.GITHUB_TOKEN)return{batch_id:null,eligible:0,attempted:0,dispatched:0,already_existing:0,dispatchErrors:1,limit:MAX_AUTOMATIC_RENDERS_PER_CYCLE,errors:["GITHUB_TOKEN eksik."]};
 const maxSuccesses=Math.max(1,Math.min(MAX_AUTOMATIC_RENDERS_PER_CYCLE,Number(limit)||MAX_AUTOMATIC_RENDERS_PER_CYCLE));
 const eligibleRow=await db.prepare("SELECT COUNT(DISTINCT d.id) AS n FROM shorts_drafts d JOIN sources s ON s.id=d.source_id JOIN creator_usage_permissions p ON p.broadcaster_id=s.twitch_broadcaster_id AND p.permission_status='approved' AND p.youtube_allowed=1 AND p.audio_rights_confirmed=1 AND trim(coalesce(p.audio_rights_evidence,''))<>'' AND trim(coalesce(p.creator_permission_evidence,''))<>'' AND p.max_source_seconds>=45 AND ((p.game_rights_basis='publisher_written_permission' AND trim(coalesce(p.game_rights_evidence_reference,''))<>'') OR (p.game_rights_basis='rockstar_noncommercial_guidelines' AND p.noncommercial_use=1)) AND (p.permission_expires_at IS NULL OR datetime(p.permission_expires_at)>datetime('now')) JOIN twitch_clip_access ta ON ta.source_id=s.id AND ta.access_status='downloadable' AND ta.download_url IS NOT NULL AND datetime(ta.checked_at)>datetime('now','-30 minutes') JOIN jobs j ON j.id=(SELECT j2.id FROM jobs j2 WHERE j2.source_id=s.id ORDER BY j2.created_at DESC LIMIT 1) WHERE s.platform='twitch' AND s.relevance_status='relevant' AND s.twitch_game_id IS NOT NULL AND s.twitch_clip_duration>=45 AND j.status IN ('queued_review','failed') AND COALESCE(j.render_attempts,0)<10 AND COALESCE(j.last_error,'') NOT LIKE '%Quality gate rejected%' AND COALESCE(j.last_error,'') NOT LIKE '%Offline quality rules rejected%'").first();
 const eligible=Number(eligibleRow?.n||0);
 const existingBatch=await db.prepare("SELECT id FROM render_batches WHERE status='active' ORDER BY created_at ASC LIMIT 1").first();
 const batchId=existingBatch?.id||uid();
 if(!existingBatch){
  await db.prepare("INSERT INTO render_batches(id,status,target_min,target_max,max_attempts,attempts,pending,published,failed,eligible) VALUES(?,'active',?,?,?,0,0,0,0,?)").bind(batchId,Math.min(MIN_AUTOMATIC_PUBLISHES_PER_CYCLE,maxSuccesses),maxSuccesses,MAX_AUTOMATIC_ATTEMPTS_PER_CYCLE,eligible).run();
 }
 const result=await fillRenderBatch(db,env,batchId,discoveryAlreadyRefreshed);
 const batch=result.batch||await db.prepare("SELECT id,status,target_min,target_max,max_attempts,attempts,pending,published,failed,eligible FROM render_batches WHERE id=?").bind(batchId).first();
 return{batch_id:batchId,batch_status:batch?.status||"unknown",target_minimum:batch?.target_min||Math.min(MIN_AUTOMATIC_PUBLISHES_PER_CYCLE,maxSuccesses),maximum_successes:batch?.target_max||maxSuccesses,eligible,attempted:result.attempted,dispatched:result.dispatched,already_existing:result.already_existing,dispatchErrors:result.dispatchErrors,not_attempted:Math.max(0,eligible-result.attempted),attempts_total:Number(batch?.attempts||0),pending:Number(batch?.pending||0),published:Number(batch?.published||0),failed:Number(batch?.failed||0),errors:result.errors};
}
async function getData(db){const sources=await db.prepare(`SELECT s.id,s.platform,s.source_url,s.creator_name,s.title,s.rights_status,s.relevance_status,s.twitch_game_id,s.twitch_broadcaster_id,a.score,a.media_quality_score,a.media_duration,a.source_width,a.source_height,a.source_fps,a.source_has_audio,a.silence_ratio,a.media_usable,a.scene_change_count,a.mean_volume_db,a.media_analyzed_at FROM sources s LEFT JOIN clip_analysis a ON a.source_id=s.id ORDER BY s.created_at DESC LIMIT 500`).all(),drafts=await db.prepare(`SELECT d.id,d.source_id,d.status,d.title,d.script,d.source_url,d.creator_name,d.created_at,s.rights_status,j.status AS job_status,j.output_key,j.package_url,j.last_error,j.youtube_status,j.youtube_url,j.thumbnail_status FROM shorts_drafts d JOIN sources s ON s.id=d.source_id LEFT JOIN jobs j ON j.source_id=d.source_id ORDER BY d.created_at DESC LIMIT 500`).all();return{sources:sources.results||[],drafts:drafts.results||[]};}
async function runScheduled(env,event){
 const started=Date.now();
 const runContext={scheduled_time:event?.scheduledTime??null,cron:event?.cron??null};
 console.log(JSON.stringify({type:"scheduled_run_started",...runContext,started_at:new Date(started).toISOString()}));
 try{
  if(!env.DB)throw new Error("D1 binding missing");
  await ensureSchema(env.DB);
  await ensureTwitchSchema(env.DB);
  let discovery,durationValidation,downloadAccess;
  try{discovery=await discover(env.DB,env);}catch(error){discovery={error:String(error&&error.message||error).slice(0,500)};}
  try{durationValidation=await validateResolvedClipDurations(env.DB,env,500);}catch(error){durationValidation={error:String(error&&error.message||error).slice(0,500)};}
  try{downloadAccess=await checkTwitchDownloads(env.DB,env,500);}catch(error){downloadAccess={error:String(error&&error.message||error).slice(0,500)};}
  const staleJobs=await env.DB.prepare("SELECT batch_id,COUNT(*) AS n FROM jobs WHERE status='processing' AND dispatch_started_at IS NOT NULL AND dispatch_started_at<datetime('now','-45 minutes') AND batch_id IS NOT NULL GROUP BY batch_id").all();
  for(const stale of staleJobs.results||[]){
   const count=Math.max(0,Number(stale.n)||0);
   if(count)await env.DB.prepare("UPDATE render_batches SET pending=MAX(0,pending-?),failed=failed+?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'").bind(count,count,stale.batch_id).run();
  }
  await env.DB.prepare("UPDATE jobs SET status='failed',last_error='Recovered stale dispatch after 45 minutes without callback.',updated_at=CURRENT_TIMESTAMP WHERE status='processing' AND dispatch_started_at IS NOT NULL AND dispatch_started_at<datetime('now','-45 minutes')").run();
  await env.DB.prepare("UPDATE shorts_drafts SET status='failed',updated_at=CURRENT_TIMESTAMP WHERE source_id IN (SELECT source_id FROM jobs WHERE status='failed' AND last_error='Recovered stale dispatch after 45 minutes without callback.')").run();
  const prepared=await prepareAll(env.DB);
  const rendering=await dispatchQueuedRenders(env.DB,env,MAX_AUTOMATIC_RENDERS_PER_CYCLE,true);
  const summary={
   type:"scheduled_run_completed",
   ...runContext,
   duration_ms:Date.now()-started,
   discovery:discovery||null,
   duration_validation:durationValidation||null,
   download_access:downloadAccess||null,
   prepared:prepared||null,
   render_batch:{
    target_minimum:rendering.target_minimum||MIN_AUTOMATIC_PUBLISHES_PER_CYCLE,
    maximum:rendering.maximum_successes||MAX_AUTOMATIC_RENDERS_PER_CYCLE,
    batch_id:rendering.batch_id||null,
    batch_status:rendering.batch_status||null,
    attempts_total:rendering.attempts_total||0,
    pending:rendering.pending||0,
    published:rendering.published||0,
    failed:rendering.failed||0,
    eligible:rendering.eligible||0,
    attempted:rendering.attempted||0,
    dispatched:rendering.dispatched||0,
    already_existing:rendering.already_existing||0,
    dispatch_errors:rendering.dispatchErrors||0,
    not_attempted:rendering.not_attempted||0
   },
   errors:rendering.errors||[]
  };
  console.log(JSON.stringify(summary));
  return{discovery,duration_validation:durationValidation,download_access:downloadAccess,prepared,...rendering};
 }catch(error){
  const failure={type:"scheduled_run_failed",...runContext,duration_ms:Date.now()-started,error:String(error&&error.message||error).slice(0,1000)};
  console.error(JSON.stringify(failure));
  return{error:failure.error};
 }
}
function makeZip(files){const enc=new TextEncoder(),local=[],central=[];let offset=0;const u16=n=>new Uint8Array([n&255,(n>>>8)&255]),u32=n=>new Uint8Array([n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255]),join=parts=>{const out=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let at=0;for(const p of parts){out.set(p,at);at+=p.length;}return out;},crc32=data=>{let c=0xffffffff;for(const b of data){c^=b;for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;};for(const f of files){const name=enc.encode(f.name),data=f.data,crc=crc32(data),lh=join([u32(0x04034b50),u16(20),u16(0x0800),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),name]);local.push(lh,data);central.push(join([u32(0x02014b50),u16(20),u16(20),u16(0x0800),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset),name]));offset+=lh.length+data.length;}const centralBytes=join(central),localBytes=join(local),end=join([u32(0x06054b50),u16(0),u16(0),u16(files.length),u16(files.length),u32(centralBytes.length),u32(localBytes.length),u16(0)]);return join([localBytes,centralBytes,end]);}
function escHtml(v){return String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
export default{async fetch(request,env){if(env.APP_ENV==="preview"){const previewPath=new URL(request.url).pathname;if(previewPath==="/__preview_health")return new Response(JSON.stringify({ok:true,environment:"preview",database:"disabled"}),{headers:{"Content-Type":"application/json","Cache-Control":"no-store"}});return new Response("Preview deployment is isolated. Database-backed routes are disabled until a dedicated staging D1 database is configured.",{status:503,headers:{"Content-Type":"text/plain; charset=utf-8","Cache-Control":"no-store"}});}try{if(!env.DB)return json({error:"D1 DB binding bulunamadı."},500);await ensureSchema(env.DB);await ensureTwitchSchema(env.DB);const url=new URL(request.url),path=url.pathname,method=request.method;
if(path==="/")return new Response(HTML,{headers:{"Content-Type":"text/html; charset=utf-8","Cache-Control":"no-store"}});
if(path==="/api/login"&&method==="POST"){const data=await readBody(request);if(!env.APP_PASSWORD||data.password!==env.APP_PASSWORD)return json({error:"Şifre hatalı."},401);const session=await makeSession(env.APP_PASSWORD);return new Response(JSON.stringify({ok:true,version:VERSION}),{headers:{"Content-Type":"application/json","Set-Cookie":"gta6_session="+session+"; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=43200"}});}
if(path==="/api/logout"&&method==="POST")return new Response(JSON.stringify({ok:true}),{headers:{"Content-Type":"application/json","Set-Cookie":"gta6_session=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0"}});
if(path==="/api/me"&&method==="GET"){if(!await authorized(request,env))return json({error:"Giriş gerekli."},401);return json({ok:true,version:VERSION});}
if(path==="/auth/twitch/callback"&&method==="GET"){const code=url.searchParams.get("code"),state=url.searchParams.get("state"),oauthError=url.searchParams.get("error"),errorDescription=url.searchParams.get("error_description")||"";if(oauthError)return new Response("<!doctype html><meta charset='utf-8'><body style='font-family:Arial;background:#0b0d12;color:white;padding:40px'><h2>Twitch bağlantısı başarısız</h2><p>"+escHtml(errorDescription||oauthError)+"</p></body>",{status:400,headers:{"Content-Type":"text/html;charset=utf-8"}});if(!code||!state)return new Response("Eksik OAuth parametresi.",{status:400});const stateRow=await env.DB.prepare("SELECT state,expires_at FROM twitch_oauth_states WHERE state=?").bind(state).first();if(!stateRow||Number(stateRow.expires_at)<Date.now())return new Response("OAuth state geçersiz veya süresi dolmuş.",{status:400});await env.DB.prepare("DELETE FROM twitch_oauth_states WHERE state=?").bind(state).run();const tokenData=await exchangeTwitchCode(code,request,env),validation=await twitchValidate(tokenData.access_token),profile=await twitchUser(tokenData.access_token,env);if(!profile||profile.id!==validation.user_id)throw new Error("Twitch kullanıcı doğrulaması başarısız.");await saveTwitchOAuth(env,tokenData,profile);return new Response("<!doctype html><meta charset='utf-8'><script>window.opener&&window.opener.postMessage({type:'twitch-connected'},location.origin);window.close();</script><body style='font-family:Arial;background:#0b0d12;color:white;padding:40px'><h2>Twitch bağlandı.</h2><p>Bu pencereyi kapatabilirsin.</p></body>",{headers:{"Content-Type":"text/html;charset=utf-8"}});}
if(path==="/api/render/callback"&&method==="POST")return await renderCallback(request,env,env.DB);
if(!await authorized(request,env)&&!(path==="/api/prepare"&&method==="POST"&&env.RENDER_WEBHOOK_SECRET&&request.headers.get("X-Render-Secret")===env.RENDER_WEBHOOK_SECRET))return json({error:"Giriş gerekli."},401);
if(path==="/api/twitch/connect"&&method==="GET"){if(!env.TWITCH_CLIENT_ID||!env.TWITCH_CLIENT_SECRET)return json({error:"Twitch Client ID/Secret Worker secret olarak bulunamadı."},500);return json({url:await createTwitchOAuthUrl(request,env)});}
if(path==="/api/twitch/status"&&method==="GET"){let row=await getTwitchOAuth(env.DB,env);if(!row)return json({connected:false,version:VERSION});let valid=false;try{await twitchValidate(row.access_token);valid=true}catch(e){try{row=await refreshTwitchOAuth(env.DB,env,row);valid=true}catch(refreshError){valid=false;}}return json({connected:valid,user_id:row.user_id,login:row.login,display_name:row.display_name,scopes:row.scopes||[],expires_at:row.expires_at,updated_at:row.updated_at,version:VERSION});}
if(path==="/api/twitch/disconnect"&&method==="POST"){await env.DB.prepare("DELETE FROM twitch_oauth WHERE id=1").run();return json({ok:true});}
if(path==="/api/twitch/clips/direct-download"&&method==="POST"){const data=await readBody(request),slug=extractClipSlug(String(data.url||"").trim());if(!slug)return json({error:"Geçerli bir Twitch klip bağlantısı gir."},400);const appToken=await twitchToken(env),clips=await twitchGet("https://api.twitch.tv/helix/clips?id="+encodeURIComponent(slug),env,appToken),clip=clips[0];if(!clip)return json({error:"Twitch klibi bulunamadı veya artık erişilebilir değil."},404);const gameId=await getGta6GameId(env,appToken),games=clip.game_id?await twitchGet("https://api.twitch.tv/helix/games?id="+encodeURIComponent(clip.game_id),env,appToken):[],gameName=String(games[0]?.name||"").trim().toLowerCase(),isGta6=(!!gameId&&String(clip.game_id||"")===String(gameId))||gameName==="grand theft auto vi"||gameName==="gta vi";if(!isGta6)return json({error:"Bu klip Twitch üzerinde GTA VI kategorisinde doğrulanmadı."},400);const connected=await userTwitchToken(env.DB,env);if(!connected)return json({error:"Önce Twitch hesabını bağla. İndirme Twitch hesabının klip erişimine bağlıdır."},401);const downloads=await fetchClipDownloads(env.DB,env,{...connected,broadcaster_id:clip.broadcaster_id},[clip.id]),entry=(downloads||[]).find(x=>x.clip_id===clip.id),downloadUrl=entry?.portrait_download_url||entry?.landscape_download_url;if(!downloadUrl)return json({error:"Twitch bu klip için MP4 indirme bağlantısı vermedi. Hesabının klip sahibi/yayıncı editörü erişimini kontrol et."},404);const file=await fetch(downloadUrl);if(!file.ok||!file.body)return json({error:"Twitch geçici MP4 bağlantısı çalışmıyor. Tekrar dene."},502);const safeName=String(clip.title||"Twitch_Klip").normalize("NFKD").replace(/[^a-zA-Z0-9_-]+/g,"_").replace(/^_+|_+$/g,"").slice(0,70)||"Twitch_Klip";return new Response(file.body,{headers:{"Content-Type":"video/mp4","Content-Disposition":"attachment; filename="+safeName+".mp4","Cache-Control":"no-store"}});}if(path==="/api/twitch/downloads/check"&&method==="POST"){const data=await readBody(request);return json(await checkTwitchDownloads(env.DB,env,data.limit||20));}
if(path==="/api/twitch/downloads/bulk.zip"&&method==="POST"){const data=await readBody(request);await checkTwitchDownloads(env.DB,env,Math.min(100,Math.max(1,Number(data.limit)||100)));const available=(await env.DB.prepare("SELECT a.source_id,a.clip_id,a.broadcaster_id,a.broadcaster_name,a.download_url,a.reason,a.checked_at,s.title,s.creator_name,s.source_url FROM twitch_clip_access a JOIN sources s ON s.id=a.source_id WHERE a.access_status='downloadable' AND a.download_url IS NOT NULL AND datetime(a.checked_at)>datetime('now','-30 minutes') ORDER BY a.checked_at DESC LIMIT 10").all()).results||[];if(!available.length)return json({error:"İndirilebilir klip bulunamadı. Önce Twitch hesabının bağlı olduğunu ve klip erişim kontrolünün başarılı olduğunu doğrula."},404);const files=[];let total=0;for(let i=0;i<available.length;i++){const x=available[i],downloadUrl=x.portrait_download_url||x.landscape_download_url;const response=await fetch(downloadUrl);if(!response.ok)continue;const bytes=new Uint8Array(await response.arrayBuffer());if(!bytes.length||bytes.length>100*1024*1024||total+bytes.length>300*1024*1024)continue;total+=bytes.length;const base=String(x.title||("GTA6_KLIP_"+(i+1))).normalize("NFKD").replace(/[^a-zA-Z0-9_-]+/g,"_").replace(/^_+|_+$/g,"").slice(0,65)||("GTA6_KLIP_"+(i+1));const source={title:x.title||"GTA VI Moment",creator_name:x.broadcaster_name||x.creator_name||"Unknown",source_url:x.source_url||""};const editorial=makeEditorialPackage(source);const meta=editorial.script+"\n\nYOUTUBE SHORTS DESCRIPTION:\n"+editorial.title+"\n\nGTA 6 gameplay moment. Watch the clip and share your reaction.\n\nSOURCE: "+source.source_url+"\nCREATOR: "+source.creator_name+"\n\nHASHTAGS:\n#GTA6 #GTAVI #Shorts #Gaming\n\nTAGS:\nGTA 6, GTA VI, GTA 6 gameplay, GTA 6 clips, gaming shorts, YouTube Shorts";const prefix=String(i+1).padStart(2,"0");files.push({name:prefix+"_"+base+".mp4",data:bytes},{name:prefix+"_"+base+".txt",data:new TextEncoder().encode(meta)});}if(!files.length)return json({error:"Twitch indirme bağlantıları süresi dolmuş veya dosyalar çok büyük. Erişim kontrolünü yenileyip tekrar dene."},502);const zip=makeZip(files);return new Response(zip,{headers:{"Content-Type":"application/zip","Content-Disposition":"attachment; filename=GTA6_SHORTS_PAKET.zip","Cache-Control":"no-store"}});}
if(path==="/api/twitch/downloads/status"&&method==="GET")return json(await getDownloadStatus(env.DB));
if(path==="/api/system/status"&&method==="GET")return json({version:VERSION,database:!!env.DB,appPassword:!!env.APP_PASSWORD,twitchClient:!!(env.TWITCH_CLIENT_ID&&env.TWITCH_CLIENT_SECRET),githubToken:!!env.GITHUB_TOKEN,renderWebhookSecret:!!env.RENDER_WEBHOOK_SECRET});
if(path==="/api/data"&&method==="GET")return json(await getData(env.DB));
if(path==="/api/permissions"&&method==="GET"){
 const rows=await env.DB.prepare("SELECT broadcaster_id,broadcaster_name,permission_status,creator_permission_evidence,audio_rights_evidence,audio_rights_confirmed,max_source_seconds,permission_expires_at,game_rights_basis,game_rights_evidence_reference,noncommercial_use,notes,updated_at FROM creator_usage_permissions ORDER BY broadcaster_name COLLATE NOCASE").all();
 return json({permissions:rows.results||[]});
}
if(path==="/api/permissions/grant"&&method==="POST"){
 const data=await readBody(request);
 const broadcasterId=String(data.broadcaster_id||"").trim();
 const broadcasterName=String(data.broadcaster_name||"").trim().slice(0,160);
 const creatorEvidence=String(data.creator_permission_evidence||"").trim().slice(0,2000);
 const audioEvidence=String(data.audio_rights_evidence||"").trim().slice(0,2000);
 const gameBasis=String(data.game_rights_basis||"").trim();
 const gameEvidence=String(data.game_rights_evidence_reference||"").trim().slice(0,2000);
 const maxSeconds=Number(data.max_source_seconds);
 const expiry=String(data.permission_expires_at||"").trim();
 const noncommercial=data.noncommercial_use===true;
 if(data.confirm_authorization!==true)return json({error:"İzin kaydını onaylamak için açık teyit gerekiyor."},400);
 if(!broadcasterId||!broadcasterName||!creatorEvidence||!audioEvidence||data.confirm_audio_rights!==true||!Number.isFinite(maxSeconds)||maxSeconds<45||maxSeconds>175)
  return json({error:"Yayıncı ID/adı, görüntü ve ses/müzik kullanım kanıtları, ses hakkı teyidi ve 45–175 saniye arası azami kullanım süresi zorunludur."},400);
 if(expiry&&(!Number.isFinite(Date.parse(expiry))||Date.parse(expiry)<=Date.now()))
  return json({error:"İzin bitiş tarihi geçerli ve gelecekte olmalı."},400);
 if(!["rockstar_noncommercial_guidelines","publisher_written_permission"].includes(gameBasis))
  return json({error:"Rockstar/Take-Two oyun görüntüsü için geçerli hak dayanağını seç."},400);
 if(gameBasis==="rockstar_noncommercial_guidelines"&&!noncommercial)
  return json({error:"Rockstar'ın genel fan kullanım politikası yalnızca non-commercial kullanım için geçerlidir; ticari/monetized kullanım için yazılı yayıncı izni gerekir."},400);
 if(gameBasis==="publisher_written_permission"&&!gameEvidence)
  return json({error:"Yayıncıdan alınmış yazılı oyun görüntüsü izninin kanıtı zorunludur."},400);
 await env.DB.prepare(`INSERT INTO creator_usage_permissions(
  broadcaster_id,broadcaster_name,permission_status,creator_permission_evidence,max_source_seconds,
  permission_expires_at,game_rights_basis,game_rights_evidence_reference,audio_rights_evidence,audio_rights_confirmed,noncommercial_use,youtube_allowed,notes,updated_at
 ) VALUES(?,?,'approved',?,?,?,?,?,?,1,?,1,?,CURRENT_TIMESTAMP)
 ON CONFLICT(broadcaster_id) DO UPDATE SET
  broadcaster_name=excluded.broadcaster_name,permission_status='approved',
  creator_permission_evidence=excluded.creator_permission_evidence,
  max_source_seconds=excluded.max_source_seconds,permission_expires_at=excluded.permission_expires_at,
  game_rights_basis=excluded.game_rights_basis,
  game_rights_evidence_reference=excluded.game_rights_evidence_reference,
  audio_rights_evidence=excluded.audio_rights_evidence,audio_rights_confirmed=1,
  noncommercial_use=excluded.noncommercial_use,youtube_allowed=1,notes=excluded.notes,updated_at=CURRENT_TIMESTAMP
 `).bind(broadcasterId,broadcasterName,creatorEvidence,maxSeconds,expiry||null,gameBasis,gameEvidence||null,audioEvidence,noncommercial?1:0,String(data.notes||"").slice(0,1000)).run();
 return json({ok:true,broadcaster_id:broadcasterId,permission_status:"approved"});
}
if(path==="/api/permissions/revoke"&&method==="POST"){
 const data=await readBody(request),id=String(data.broadcaster_id||"").trim();
 if(!id)return json({error:"broadcaster_id required"},400);
 await env.DB.prepare("UPDATE creator_usage_permissions SET permission_status='revoked',youtube_allowed=0,updated_at=CURRENT_TIMESTAMP WHERE broadcaster_id=?").bind(id).run();
 return json({ok:true,permission_status:"revoked"});
}
if(path==="/api/discover"&&method==="POST")return json(await discover(env.DB,env));

if(path==="/api/prepare"&&method==="POST"){let discovery,downloadAccess;try{discovery=await discover(env.DB,env);}catch(error){discovery={error:String(error&&error.message||error).slice(0,500)};}const clipValidation=await resolveTwitchClips(env.DB,env,500);const durationValidation=await validateResolvedClipDurations(env.DB,env,500);try{downloadAccess=await checkTwitchDownloads(env.DB,env,500);}catch(error){downloadAccess={error:String(error&&error.message||error).slice(0,500)};}const prepared=await prepareAll(env.DB);const rendering=await dispatchQueuedRenders(env.DB,env,10,true);return json({...prepared,discovery,clip_validation:clipValidation,duration_validation:durationValidation,download_access:downloadAccess,rendering});}
if(path==="/api/render/dispatch"&&method==="POST"){const data=await readBody(request);const result=await dispatchRender(env.DB,env,String(data.draft_id||""),data.evidence_reference,data.authorization_confirmation);return result.error?json({error:result.error},400):json(result);}
if(path==="/api/source/quick"&&method==="POST"){
if(!await authorized(request,env))return json({error:"Giriş gerekli."},401);
const data=await readBody(request),clipUrl=String(data.url||"").trim();
let clipSlug=null;
try{const u=new URL(clipUrl),host=u.hostname.toLowerCase().replace(/^www\./,"");if(host==="clips.twitch.tv")clipSlug=u.pathname.split("/").filter(Boolean)[0]||null;else if(host==="twitch.tv"){const p=u.pathname.split("/").filter(Boolean),i=p.findIndex(x=>x.toLowerCase()==="clip");if(i>=0&&p[i+1]&&!p[i+2])clipSlug=p[i+1];}}catch{}
if(!clipSlug)return json({error:"Geçerli bir Twitch klip bağlantısı yapıştır. Örnek: twitch.tv/yayıncı/clip/KlipKodu"},400);

const appToken=await twitchToken(env),clipRows=await twitchGet("https://api.twitch.tv/helix/clips?id="+encodeURIComponent(clipSlug),env,appToken),clip=clipRows[0];
if(!clip)return json({error:"Twitch bu klibi bulamadı veya klip artık erişilebilir değil."},404);
if(Number(clip.duration||0)<45)return json({error:"Klip 45 saniyeden kısa; kanalın minimum video süresi nedeniyle üretim başlatılmadı."},400);
const gameId=await getGta6GameId(env,appToken),clipGameRows=clip.game_id?await twitchGet("https://api.twitch.tv/helix/games?id="+encodeURIComponent(clip.game_id),env,appToken):[],clipGameName=String(clipGameRows[0]?.name||"").trim().toLowerCase();
const categoryConfirmed=(!!gameId&&String(clip.game_id||"")===String(gameId))||clipGameName==="grand theft auto vi"||clipGameName==="gta vi";
if(!categoryConfirmed)return json({error:"Bu klibin Twitch kategorisi GTA VI olarak doğrulanamadı ("+(clipGameRows[0]?.name||"kategori boş")+"). MP4 üretimi başlatılmadı."},400);
const canonicalUrl="https://www.twitch.tv/"+String(clip.broadcaster_name||"channel").toLowerCase()+"/clip/"+clip.id;
let source=await env.DB.prepare("SELECT id FROM sources WHERE twitch_clip_id=? OR source_url=? LIMIT 1").bind(clip.id,canonicalUrl).first(),sourceId;
if(source){sourceId=source.id;await env.DB.prepare("UPDATE sources SET platform='twitch',source_url=?,creator_name=?,title=?,rights_status='pending',twitch_clip_id=?,twitch_broadcaster_id=?,twitch_game_id=?,twitch_clip_duration=?,relevance_status='relevant' WHERE id=?").bind(canonicalUrl,clip.broadcaster_name||"Twitch",clip.title||"GTA VI clip",clip.id,clip.broadcaster_id,clip.game_id||null,Number(clip.duration||0),sourceId).run();}
else{sourceId=uid();await env.DB.prepare("INSERT INTO sources(id,platform,source_url,creator_name,title,rights_status,twitch_clip_id,twitch_broadcaster_id,twitch_game_id,twitch_clip_duration,relevance_status) VALUES(?,'twitch',?,?,?,'pending',?,?,?,?,'relevant')").bind(sourceId,canonicalUrl,clip.broadcaster_name||"Twitch",clip.title||"GTA VI clip",clip.id,clip.broadcaster_id,clip.game_id||null,Number(clip.duration||0)).run();}
await analyzeSource(env.DB,{id:sourceId,title:clip.title||"GTA VI clip"},clip.view_count||0,clip.duration||30);
const prepared=await prepareAll(env.DB),draft=await env.DB.prepare("SELECT id FROM shorts_drafts WHERE source_id=? LIMIT 1").bind(sourceId).first();
if(!draft)return json({error:"Klip doğrulandı ancak üretim paketi oluşturulamadı.",prepared},400);
const result=await dispatchRender(env.DB,env,draft.id,"","owner-confirmed");
return result.error?json({error:result.error},400):json({ok:true,job_id:result.job_id,draft_id:draft.id,status:result.status,prepared});
}
if(path==="/api/source/manual"&&method==="POST"){const data=await readBody(request);if(!data.url||!/^https?:\/\//i.test(data.url))return json({error:"Geçerli bir kaynak URL gir."},400);const exists=await env.DB.prepare("SELECT id FROM sources WHERE source_url=? LIMIT 1").bind(data.url).first();if(exists)return json({error:"Bu kaynak zaten kayıtlı."},409);const id=uid(),title=data.title||"Untitled",isRelevant=isGta6Relevant(title);await env.DB.prepare(`INSERT INTO sources(id,platform,source_url,creator_name,title,rights_status,relevance_status) VALUES(?,?,?,?,?,'pending',?)`).bind(id,"manual",data.url,data.creator||"Unknown",title,isRelevant?"relevant":"unknown").run();await analyzeSource(env.DB,{id,title});return json({ok:true,id,relevance_status:isRelevant?"relevant":"unknown"});}
return json({error:"Endpoint bulunamadı.",version:VERSION},404);
}catch(error){return json({error:error&&error.message?error.message:"Bilinmeyen sunucu hatası.",version:VERSION},500);}},async scheduled(event,env,ctx){const work=runScheduled(env,event);if(ctx&&typeof ctx.waitUntil==="function")ctx.waitUntil(work);else await work;}};