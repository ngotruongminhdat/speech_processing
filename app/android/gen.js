// Sinh dự án Android (Trusted Web Activity) từ manifest của trang đã deploy, không cần hỏi đáp.
const path = require('path');
const { TwaManifest, TwaGenerator, ConsoleLog } = require('@bubblewrap/core');
(async () => {
  const url = 'https://ngotruongminhdat.github.io/speech_processing/manifest.webmanifest';
  const m = await TwaManifest.fromWebManifest(url);
  m.packageId = 'io.github.ngotruongminhdat.sachnoi';
  m.name = 'Sách Nói';
  m.launcherName = 'Sách Nói';
  m.appVersionName = '1.0.0';
  m.appVersionCode = 1;
  m.signingKey = { path: path.resolve(__dirname, 'twa/android.keystore'), alias: 'sachnoi' };
  m.fallbackType = 'customtabs';
  m.enableNotifications = false;
  m.minSdkVersion = 24;      // thư viện androidbrowserhelper 2.7 đòi Android 7 trở lên
  m.generatorApp = 'bubblewrap-cli';
  console.log(JSON.stringify({ host: m.host, startUrl: m.startUrl, display: m.display, icon: m.iconUrl, maskable: m.maskableIconUrl, theme: m.themeColor.hex?.() }, null, 1));
  const err = m.validate();
  if (err) throw new Error(err);
  const dir = path.resolve(__dirname, 'twa');
  await m.saveToFile(path.join(dir, 'twa-manifest.json'));
  await new TwaGenerator().createTwaProject(dir, m, new ConsoleLog('gen'));
  // ghi mã kiểm của manifest, để `bubblewrap build` không hỏi lại chuyện cập nhật dự án và số phiên bản
  const sum = require('crypto').createHash('sha1').update(require('fs').readFileSync(path.join(dir, 'twa-manifest.json'))).digest('hex');
  require('fs').writeFileSync(path.join(dir, 'manifest-checksum.txt'), sum);
  console.log('ok');
})().catch((e) => { console.error(e); process.exit(1); });
