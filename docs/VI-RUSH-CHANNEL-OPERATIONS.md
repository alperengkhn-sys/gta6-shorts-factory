# VI RUSH — Kanal ve yayın operasyon kılavuzu

Bu belge, otomatik fabrikanın teknik kapılarını ve YouTube kanalındaki 53 mevcut videonun incelenme sırasını açıklar. Hiçbir izlenme, keşfet veya viral sonuç garanti edilmez.

## 1. Yayın öncesi zorunlu eleme

Her Twitch kaynağı aşağıdaki sırayla kontrol edilir:

1. Twitch klibinin gerçekten GTA VI kategorisinde olduğu doğrulanır.
2. Yayıncı kimliği üzerinden YouTube'da yeniden kullanım izni kaydı aranır.
3. İzin belgesindeki veya yazılı mesajdaki azami kaynak görüntüsü süresi kontrol edilir. Render, bu saniyeyi aşamaz.
4. Yayıncı sesi ve klipteki müzik/diğer sesler için ayrı hak kanıtı aranır.
5. GTA VI görüntüsünün yayın hakkı ayrıca değerlendirilir.
6. Son 9:16 kadrajda kalıcı yayıncı face-cam, ağır bulanıklık ve teknik bozukluk taranır.
7. Görüntü karelerinden içerik parmak izi çıkarılır. Önceden yayımlanmış aynı görüntüyle yeterince benzer ve aynı sırada eşleşirse aday reddedilir.
8. Yalnızca bu kapıları geçen klip 9:16 MP4'e dönüştürülür ve YouTube'a gönderilir.

Yayıncıdan alınan izin, Rockstar/Take-Two'nun oyun görüntüsü haklarını veya videodaki üçüncü taraf müziğin lisansını otomatik olarak vermez. Twitch'in indirme/paylaşma özelliği de tek başına YouTube ve ticari kullanım için bir lisans sayılmaz.

Rockstar'ın kamuya açık fan politikası genel olarak yalnızca non-commercial kullanımı kapsar. Videodan para kazanılan veya içeriğin bir ürün/hizmet tanıtımında kullanıldığı bir kanal için bu genel politika yeterli kabul edilmemelidir; yazılı yayıncı/lisans izni gerekir. Hak durumu belirsiz klipler yayımlanmaz. Resmî politika: https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material

## 2. Görüntü ve kapak standardı

- İlk kare bulanık olmamalıdır.
- 9:16 orta kadrajın ilk 8 saniyesi içinden en net kare kapak olarak seçilir.
- Başlık metni kısa, okunaklı ve yüksek kontrastlı olmalıdır.
- Sabit kapak geçişi 0,30 saniyedir; oyun görüntüsü hemen ardından başlar.
- Yüz/kamera kutusu, bulanıklık ve görsel tekrar kontrolleri kaynak seçimini etkiler.
- Bu filtreler yerel OpenCV sezgisel kontrolleridir; yüzleri veya bulanıklığı yüzde 100 doğrulukla sınıflandıran bir yapay zekâ garantisi değildir. Belirsiz/şüpheli klipler insan incelemesine alınmalıdır.

Shorts kapağı için YouTube'un güncel yardım sayfası ve Studio'nun izin verdiği yol izlenir. YouTube API'si Shorts için özel kapak yüklemeyi destekler; fakat API çağrısı ancak video işleme durumu `succeeded` olduktan sonra yapılmalıdır. Kanalın OAuth yetkisi/hesap uygunluğu da gerekir:
- https://support.google.com/youtube/answer/72431
- https://developers.google.com/youtube/data-api/reference/rest/v3/thumbnails/set

## 3. Başlık standardı

Hedef uzunluk: 40–60 karakter. Her başlık gerçek klipte görülen olaya dayanmalı; başlıkta görünmeyen bir kaza, polis kovalamacası, gizli detay veya karakter davranışı varmış gibi yazılmamalıdır. Aynı kaynak olayı farklı kelimelerle tekrar tekrar paketlenmemelidir.

20 örnek — bunlar yalnızca ilgili olay gerçekten klipte varsa kullanılmalıdır:

1. GTA 6 Police Chase Turns Into a Close Escape
2. One Wrong Turn Changes This GTA 6 Night Drive
3. A GTA 6 Crash Nobody Saw Coming on Vice City Streets
4. This GTA 6 NPC Reaction Is Perfectly Timed
5. The Hidden Detail in This GTA 6 Street Scene
6. GTA 6: The Fastest Way to Lose the Cops?
7. This GTA 6 Getaway Almost Goes Wrong at Night
8. A Strange GTA 6 Encounter on Vice City Streets
9. How This GTA 6 Chase Ends Is Not What You Expect
10. GTA 6: A Split-Second Decision During a Fight
11. This GTA 6 Traffic Moment Gets Out of Control
12. The Detail That Makes This GTA 6 Scene Stand Out
13. A Risky GTA 6 Escape Through Vice City Streets
14. GTA 6 Nightlife: One Moment Worth a Second Look
15. Did You Catch This GTA 6 Character Detail?
16. This GTA 6 Driving Mistake Was Costly in Vice City
17. A GTA 6 Police Stop Takes a Sudden Turn in Vice City
18. Watch What Happens During This GTA 6 Mission
19. The Most Unexpected Turn in This GTA 6 Clip
20. A GTA 6 Stream Moment With Perfect Timing

## 4. Açıklama ve etiket standardı

Her videoda ilk iki satır klibin gerçek konusunu anlatır. Ardından izleyiciye tek bir doğal soru, VI RUSH'a abone olma çağrısı, gerçek yayıncı kredisi ve 3–5 ilgili hashtag gelir.

Örnek şablon:

```text
[Specific event] in Grand Theft Auto VI (GTA 6).
[One short, accurate sentence describing what actually happens.]

What would you have done in this moment?
Subscribe to VI RUSH for more GTA VI clips and gameplay.

Clip creator: [Verified creator name]
Original source: [Twitch clip URL]

#GTA6 #GTAVI #[ActualTopic] #Shorts
```

Etiket seçimi:
- Temel: GTA 6, GTA VI, Grand Theft Auto VI.
- Olayla ilgili uzun kuyruk: GTA 6 police chase, GTA 6 Vice City car crash, GTA 6 NPC reaction gibi, yalnızca gerçekten uyuyorsa.
- Yayıncı/kanal adı yalnızca doğru ve izin kapsamı uygunsa.
- Hashtag'ler 3–5 adetle sınırlı, videonun gerçek konusuyla ilgili olmalıdır. "Trend" görünmek için alakasız hashtag eklenmez.

Önemli: YouTube, başlık, kapak ve açıklamanın keşif açısından etiketlerden daha önemli olduğunu; etiketlerin genellikle sınırlı rol oynadığını söylüyor. Etiketleri spam gibi doldurmak yerine doğru yazım/alternatif arama terimleri için kullanın:
https://support.google.com/youtube/answer/146402

## 5. İlk 53 videonun güvenli toplu denetim sırası

Hiçbir videoyu otomatik olarak silme, yeniden yükleme veya Content ID uyuşmazlığına itiraz etme. Önce YouTube Studio'da her videonun gerçek durumunu kontrol edin.

1. Content > Restrictions alanında videoları "Copyright" durumuna göre ayırın.
2. Content ID claim, bölgesel/global block, takedown ve copyright strike kayıtlarını ayrı gruplara ayırın.
3. Claim ayrıntısında hak sahibini, eşleşen ses/görüntü bölümünü ve ülke politikasını kaydedin.
4. Kaynak klip, yayıncı kullanım izni, izin verilen saniye ve ses/müzik lisansını eşleştirin.
5. İzin süresi aşılmışsa yalnızca izin verilen süreye göre yeni bir kurgu hazırlayın; hak kanıtı yoksa videoyu yayıma geri döndürmeyin.
6. Content ID müzik eşleşmesi varsa, hakkınız yoksa müziği YouTube'un izin verdiği yöntemle kaldırın/değiştirin veya klibi kullanmayın.
7. Haklar doğrulandıktan sonra başlık, açıklama, etiket ve kapakları video başına özgünleştirin.
8. Değişikliği kaydedip Studio'daki Restrictions durumunu tekrar kontrol edin.
9. Geçerli claim varsa yalnızca tüm gerekli haklara sahip olduğunuz veya claim'in yanlış olduğu kanıtlanabiliyorsa itiraz edin.
10. Takedown/strike varsa sıradan Content ID claim gibi ele almayın; retraction veya geçerli counter-notification için resmî süreci izleyin.

Content ID claim videoyu engelleyebilir, para kazanmayı hak sahibine yönlendirebilir veya sadece takip edebilir. Copyright strike ise geçerli bir telif kaldırma talebiyle ilgilidir ve farklı sonuçları vardır. 1–3 dakika arasındaki Shorts'ta aktif Content ID claim varsa video engellenebilir:
- https://support.google.com/youtube/answer/6013276
- https://support.google.com/youtube/answer/2814000
- https://support.google.com/youtube/answer/15424877

## 6. Yayın öncesi 10 maddelik kontrol listesi

- [ ] GTA VI kategorisi Twitch verisiyle doğrulandı.
- [ ] Yayıncı kimliği ve YouTube yeniden kullanım izni kanıtı kayıtlı.
- [ ] Rockstar/Take-Two oyun görüntüsü hak dayanağı kontrol edildi.
- [ ] Yayıncı sesi ve tüm müzik/arka plan sesleri için ayrı hak kaydı var.
- [ ] Kaynak görüntüsü süresi kayıtlı izin sınırını aşmıyor.
- [ ] Kalıcı yayıncı face-cam veya istenmeyen insan kamera katmanı bulunmuyor.
- [ ] Oyun görüntüsü net; ağır blur veya decode sorunu yok.
- [ ] Görsel parmak izi geçmiş yayınlarla karşılaştırıldı; aynı klip daha önce yayımlanmamış.
- [ ] İlk kare/kapak keskin ve başlık içerikle birebir uyumlu.
- [ ] Başlık, açıklama, kredi ve hashtag'ler videoya özgü; yayın sonrası hak/claim sonucu izleniyor.

## 7. YouTube Studio'da bakılacak 5 performans ölçütü

1. **Shown in feed:** Short'un Shorts akışında kaç kez gösterildiği. Gösterim var ama izlenme azsa ilk kare, konu veya açılış zayıf olabilir.
2. **How many chose to view / Stayed to watch:** İzleyenlerle kaydırıp geçenlerin oranı. Düşükse ilk 1–2 saniyenin konusunu ve ilk kareyi değiştirin.
3. **Engaged views:** İlk saniyeleri geçip izlemeye devam eden izleyiciler. Bu sayı yükselmiyorsa kanca/olay geç başlıyor olabilir.
4. **Average view duration ve Average percentage viewed:** İzleyicinin ne kadar kaldığı. Düşüşün olduğu noktada gereksiz intro, tekrar, sessizlik veya bağlam kaybı olabilir.
5. **Subscribers gained, likes ve comments:** Hangi konu/formatın gerçek izleyiciye ve aboneye dönüştüğünü gösterir.

YouTube Studio > Analytics > Content > Shorts ve her Short'un Engagement raporunu kullanın. "Shown in feed", "How many chose to view", "Engaged views", "Average view duration" ve "Average percentage viewed" resmî Shorts ölçütleridir:
https://support.google.com/youtube/answer/12942217
https://support.google.com/youtube/answer/12220281

## 8. Büyüme ve yayın temposu

- İlk 1–2 saniyede gerçek olayın en ilginç kısmına girin; uzun logo, boş kart veya yapay "wait for it" kullanmayın.
- Tek bir sabit şablonu klipten klibe kopyalamayın. İçerik ve editoryal katkı gerçekten değişmeli.
- Sırf 60 saniyeyi doldurmak için görüntü uzatmayın. İzin verilen kaynak süresi ve klibin kendi hikâyesi süreyi belirlesin.
- Yükleme saati ve sıklığını varsayım ile değil, Audience raporundaki izleyicilerin YouTube'da aktif olduğu zamanlarla test edin.
- Telifli yayıncı müziğini otomatik olarak "güvenli" saymayın; kaynak sesinin hakları ayrı kontrol edilir.
- İzlenme düşüşünü yalnızca başlığa bağlamayın; izleyici seçimi, izlenme süresi ve izleyici memnuniyetini birlikte okuyun.

## 9. Bilinen entegrasyon sınırı

Mevcut YouTube OAuth refresh token testi yalnızca `youtube.upload` iznini doğruladı. Böylece yeni video yükleme yapılabilir; fakat API ile Shorts işleme durumunu okumak, eski video metadata'sını güncellemek veya kanal Analytics API'sinden rapor çekmek için ek OAuth kapsamı gerekir. Gerekli kapsamları ekleyip kanala yeniden OAuth izni verilmeden 53 videoyu API üzerinden güvenli şekilde toplu düzenleme veya Analytics raporu çekme iddiasında bulunmayın.

Eski videolardaki gerçek claim/strike ayrıntıları YouTube Studio'dan alınmalıdır. Yeni render filtresi önceki telif iddialarını ortadan kaldırmaz.
