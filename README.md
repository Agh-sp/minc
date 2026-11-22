# سرور Minecraft Survival و TLauncher

پروژه یک سرور **Paper 1.20.4** با لابی و دنیای Survival جدا راه می‌اندازد. تنظیمات برای میزبان کوچک با سقف ۲ GiB حافظه، whitelist، ورود آفلاین با AuthMe، رابط Finglish و پشتیبانی گسترده از نسخه‌های مختلف **Java Edition** در نظر گرفته شده است. BedWars و Roleplay همچنان قفل هستند و world/plugin آن‌ها نصب نمی‌شود.

## انتخاب نسخه و راهنمایی‌های سخت‌افزاری

- سرور: Paper `1.20.4`، روی Java `21`.
- Java 21 از Java 17 جدیدتر است و برای Paper 1.20.4 اجرا می‌شود؛ WorldEdit 7.3.9 که همراه WorldGuard نصب می‌شود نیز با این runtime انتخاب شده است.
- تصویر Docker حداکثر ۲ GiB حافظه می‌گیرد و heap جاوا حداکثر 1536 MiB است. برای همین سقف بازیکن روی ۴ گذاشته شده، نه ۱۰–۲۰ نفر. افزایش ظرفیت باید همراه RAM اختصاصی بیشتر، CPU تک‌هسته‌ای قوی و SSD/NVMe باشد.
- `VIEW_DISTANCE=6` و `SIMULATION_DISTANCE=4` محافظه‌کارانه‌اند تا بار لود chunk کم بماند.

راهنمایی که فرستادی دربارهٔ Paper، RAM، فاصلهٔ دید، پورت، EULA و plugins بررسی شد. نکتهٔ شبکه‌اش برای میزبانی خانگی هم مهم است: اگر پشت CGNAT باشی، Port Forwarding مودم به‌تنهایی کافی نیست. برای Java Edition عادی پورت Minecraft روی **TCP** است؛ در این پروژه فقط TCP `25565` منتشر می‌شود.

## ورود آفلاین و محدودیت AuthMe

برای TLauncher مقدار `online-mode=false` تنظیم شده و `ENFORCE_SECURE_PROFILE=false` است تا کلاینت آفلاین بتواند وصل شود. چون این حالت مالکیت نام را از Microsoft/Mojang استعلام نمی‌کند:

- whitelist روشن است؛ فقط usernameهایی که در `.env` وارد می‌کنی می‌توانند وصل شوند.
- AuthMe از رمز حسابی که ثبت شده محافظت می‌کند، اما نمی‌تواند ثابت کند اولین کسی که نامی را ثبت می‌کند صاحب واقعی آن نام است.
- ادمین اول وارد شود و `/register <password> <password>` را انجام دهد. بهتر است دوستان هم پیش از عمومی‌کردن آدرس وارد شوند و حسابشان را ثبت کنند.
- از رمز منحصربه‌فرد و قوی استفاده کنید؛ رمز را در چت عمومی نفرستید.

سرور فقط زمانی پورت عمومی را باز می‌کند که AuthMe و همهٔ پلاگین‌های ضروری لود شده باشند و تنظیمات امنیتی اعمال شده باشد. اگر هرکدام آماده نشود، سرور متوقف می‌شود و روی اینترنت باز نمی‌ماند.

## نسخه‌های مختلف کلاینت

این سرور Java Edition است و این سه پلاگین نصب می‌شوند:

- ViaVersion: وصل‌شدن کلاینت‌های جدیدتر به سرور 1.20.4.
- ViaBackwards: پشتیبانی از کلاینت‌های قدیمی‌تر.
- ViaRewind: گسترش پشتیبانی برای بعضی کلاینت‌های 1.7/1.8-era.

در نتیجه دامنهٔ نسخه‌های Java بسیار گسترده است و بازیکن معمولاً لازم نیست چیزی روی کلاینت نصب کند. با این حال، ترجمهٔ پروتکل تضمین نمی‌کند *هر* نسخه، modpack، کلاینت دستکاری‌شده یا feature جدید دقیقاً بدون محدودیت کار کند؛ نسخه‌های خیلی متفاوت ممکن است تفاوت آیتم/رفتار داشته باشند. Bedrock در این تنظیمات فعال نیست؛ برای آن Geyser/Floodgate و تصمیم‌های جداگانه دربارهٔ احراز هویت لازم است.

## پلاگین‌ها و دسترسی دنیاها

- **AuthMe 5.7.0 + ProtocolLib 5.3.0**: ثبت‌نام/ورود آفلاین با BCRYPT، رمز ۸ تا ۶۴ کاراکتری، محدودیت حرکت، و محافظت inventory و tab-completion تا زمان login. پیام‌های اصلی Finglish هستند.
- **Multiverse-Core 5.8.2**: لابی و Survival را در worldهای جدا نگه می‌دارد.
- **LuckPerms 5.5.71**: گروه پیش‌فرض فقط اجازهٔ ورود و teleport به lobby و Survival دارد؛ دسترسی BedWars و Roleplay صریحاً بسته است. Teleportهای pluginها هم با Multiverse access check می‌شوند.
- **GriefPrevention 16.18.3**: claim برای دنیای Survival؛ claim در lobby خاموش است.
- **HuskHomes 4.11.1**: home، back، teleport request و RTP؛ RTP در lobby و worldهای وابسته به آن و worldهای Nether/End مسدود شده است. ادمین پس از ورود در lobby یک‌بار `/setspawn` بزند تا `/spawn` هم مقصد داشته باشد.
- **WorldEdit 7.3.9 + WorldGuard 7.0.9**: WorldGuard روی global region لابی، ساخت‌وساز و PvP را می‌بندد و تعامل‌های معمول را باز می‌گذارد.
- **PlaceholderAPI 2.12.3 + DeluxeMenus 1.14.1**: منوی `/menu` با متن Finglish؛ Survival باز است و BedWars/Roleplay فقط به‌صورت گزینه‌های قفل‌شده نمایش داده می‌شوند.
- **ViaVersion 5.12.2 + ViaBackwards 5.12.2 + ViaRewind 4.2.0**: ترجمهٔ پروتکل کلاینت‌های مختلف.

EssentialsX عمداً نصب نشده چون HuskHomes همین قابلیت‌های اصلی خانه و teleport را می‌دهد و هم‌پوشانی commandها کمتر می‌ماند.

برای اضافه‌کردن plugin: فقط نسخه‌ای را انتخاب کن که با Paper 1.20.4/Java 21 سازگار باشد؛ URL نسخهٔ ثابت را به فهرست `PLUGINS` در `docker-compose.yml` اضافه کن، یا JAR را در پوشهٔ `plugins/` بگذار، سپس با `./stop.sh` و `./start.sh` سرور را دوباره راه‌اندازی کن. فایل‌های JAR در Git نادیده گرفته می‌شوند؛ plugin را فقط از منبعی که به آن اعتماد داری بگیر و پیش از تغییر از `data/` پشتیبان تهیه کن.

## راه‌اندازی روی Ubuntu

پیش‌نیازها: Docker Engine، Docker Compose v2، Python 3، و فضای کافی روی SSD. راهنمای نصب Docker برای Ubuntu: <https://docs.docker.com/engine/install/ubuntu/>.

1. پوشهٔ پروژهٔ دیگر را استفاده نکن و هیچ‌وقت `data/` دو سرور را share نکن. از ترمینال کامپیوترت اول روی سرور پوشه‌ای جدا بساز:

   ```bash
   ssh SERVER_USER@SERVER_IP 'mkdir -p ~/servers/minc-survival'
   ```

   بعد، از داخل پوشهٔ همین پروژه، فایل‌های پروژه را منتقل کن (به‌جای مقادیر نمونه SSH user/IP خودت را بگذار):

   ```bash
   rsync -av --exclude='.git/' --exclude='.env' --exclude='data/' --exclude='backups/' --exclude='portainer-data/' ./ SERVER_USER@SERVER_IP:~/servers/minc-survival/
   ```

   فایل `.env` و `data/` روی سرور جداگانه ساخته می‌شوند؛ `.env` را از پروژهٔ دیگر کپی نکن. این Compose project با نام `minc-survival` اجرا می‌شود. اگر پورت `25565` دست پروژهٔ دیگری است، آن را نگه دار و برای این سرور یک پورت آزاد دیگر در `.env` بگذار؛ اسکریپت تداخل پورت را هم بررسی می‌کند.
2. در سرور اجرا کن:

   ```bash
   chmod +x start.sh stop.sh scripts/*.sh
   ./start.sh
   ```

3. بار اول username ادمین، نام‌های whitelist، پورت و تأیید خواندن EULA پرسیده می‌شود. اسم‌ها را با کاما جدا کن؛ مثلاً `AdminName,FriendOne,FriendTwo`.
4. آدرس سرور را به بازیکنان بده. آن‌ها با هر نسخهٔ Java سازگار که Via بتواند ترجمه کند وصل می‌شوند، سپس `/register <password> <password>` و دفعات بعد `/login <password>` را می‌زنند.
5. برای انتخاب حالت `/menu` را باز کنند. Survival utilities شامل `/sethome`, `/home`, `/tpa` و `/rtp` است.

برای لاگ سرور:

```bash
docker compose logs -f survival
```

برای توقف امن Minecraft:

```bash
./stop.sh
```

`data/` شامل دنیاها، دیتابیس AuthMe، تنظیمات pluginها و فایل‌های سرور است و در Git ذخیره نمی‌شود. نقشهٔ BedWars یا Roleplay هنوز نصب نشده و برای این دو حالت world ساخته نمی‌شود.

## پورت، فایروال و دسترسی از اینترنت

پورت پیش‌فرض Java Edition، TCP `25565` است. اگر UFW یا فایروال ارائه‌دهنده فعال است:

```bash
sudo ufw allow 25565/tcp
```

اگر روی شبکهٔ خانگی میزبانی می‌کنی، باید TCP `25565` را در router به IP ثابت LAN سرور forward کنی. اگر ISP پشت CGNAT باشد یا IPv4 عمومی ندهد، port forwarding کار نمی‌کند؛ راهکارها VPS/public IP یا relay مناسب‌اند. پورت RCON و پنل مدیریت در اینترنت publish نشده‌اند. اگر `MC_PORT` را در `.env` تغییر دادی، قانون firewall و router را هم هماهنگ کن.

## پنل مدیریت خصوصی

Portainer فقط در پروفایل جدا اجرا می‌شود و پورت آن به `127.0.0.1` محدود است:

```bash
./scripts/start-panel.sh
```

از رایانهٔ خودت یک تونل SSH باز نگه دار:

```bash
ssh -N -L 8765:127.0.0.1:8765 SSH_USER@SERVER_IP
```

سپس <http://localhost:8765/panl/> را باز کن و در اولین ورود حساب مدیر را خودت بساز. برای توقف پنل:

```bash
./scripts/stop-panel.sh
```

پنل به Docker دسترسی مدیریتی کامل دارد؛ ممکن است کانتینرهای دیگر، ازجمله بازی فعلی، را هم نشان دهد. فقط سرویس Minecraft را مدیریت کن و پنل را مستقیم و بدون HTTPS روی اینترنت عمومی باز نکن.

## پشتیبان‌گیری

پیش از تغییر بزرگ یا نصب map، سرور را متوقف و از `data/` نسخهٔ پشتیبان بگیر:

```bash
./stop.sh
tar -czf "minc-backup-$(date +%F-%H%M).tar.gz" data/
```

## منابع

- [راهنمایی که فرستادی: ساخت سرور Minecraft با اینترنت ملی](https://ferdowsi.cloud/blog/minecraft-server-setup/)
- [AuthMeReloaded](https://github.com/AuthMe/AuthMeReloaded)
- [Multiverse-Core: permissionها](https://github.com/Multiverse/Multiverse-Core/wiki/Permissions)
- [ViaVersion](https://hangar.papermc.io/ViaVersion/ViaVersion)
- [GriefPrevention: پیکربندی](https://docs.griefprevention.com/configuration/)
- [ProtocolLib](https://github.com/dmulloy2/ProtocolLib/releases)
- [DeluxeMenus: commands and permissions](https://wiki.helpch.at/helpchat-plugins/deluxemenus/commands-and-permissions)
- [WorldGuard: region flags](https://worldguard.enginehub.org/en/latest/regions/flags/)
- [WorldGuard: فرمان‌های region](https://worldguard.enginehub.org/en/latest/regions/commands/)
- [Docker Minecraft Server](https://github.com/itzg/docker-minecraft-server)
