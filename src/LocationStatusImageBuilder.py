from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import math
import os


# ─────────────────────────────────────────────
#  Palette (from Modiin emblem)
# ─────────────────────────────────────────────
C_BG_TOP   = (14,  62,  50)
C_BG_BOT   = ( 8,  35,  28)
C_TEAL     = (43, 169, 139)
C_TEAL_LT  = (80, 200, 165)
C_WHITE    = (255, 255, 255)
C_CREAM    = (235, 245, 238)
C_GOLD     = (255, 210,  80)
C_BLUE_LT  = (130, 200, 255)
C_GRAY     = (160, 195, 180)

FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG  = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def fnt(size, bold=True):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def text_center(d, cx, y, text, font, fill):
    bb = d.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    d.text((cx - w//2, y), text, font=font, fill=fill)


# ─────────────────────────────────────────────
#  Gradient background
# ─────────────────────────────────────────────
def gradient_bg(w, h):
    img = Image.new('RGB', (w, h))
    px = img.load()
    for y in range(h):
        t = y / h
        r = int(C_BG_TOP[0]*(1-t) + C_BG_BOT[0]*t)
        g = int(C_BG_TOP[1]*(1-t) + C_BG_BOT[1]*t)
        b = int(C_BG_TOP[2]*(1-t) + C_BG_BOT[2]*t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


# ─────────────────────────────────────────────
#  Weather icons (pure Pillow)
# ─────────────────────────────────────────────
def icon_sun(d, cx, cy, r, color=C_GOLD):
    rd = int(r * 0.44)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        x1 = cx + int((rd+3)*math.cos(rad)); y1 = cy + int((rd+3)*math.sin(rad))
        x2 = cx + int((r-2)*math.cos(rad));  y2 = cy + int((r-2)*math.sin(rad))
        d.line([(x1,y1),(x2,y2)], fill=color, width=max(2, r//12))
    d.ellipse([cx-rd, cy-rd, cx+rd, cy+rd], fill=color)

def icon_moon_crescent(d, cx, cy, r, color=C_GOLD, bg=C_BG_TOP):
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    d.ellipse([cx+r//5, cy-r, cx+r//5+r*2, cy+r], fill=bg)

def icon_cloud(d, cx, cy, r, color=C_GRAY):
    cr = int(r*0.40)
    bx, by = cx, cy + int(r*0.12)
    d.ellipse([bx-cr, by-cr//2, bx+cr, by+cr//2], fill=color)
    d.ellipse([bx-cr+4, by-cr, bx+cr+4, by+4], fill=C_WHITE)
    d.ellipse([bx+int(cr*0.5), by-int(cr*0.75), bx+int(cr*0.5)+cr, by+int(cr*0.4)], fill=color)

def icon_partly(d, cx, cy, r):
    icon_sun(d, cx+int(r*0.22), cy-int(r*0.22), int(r*0.56))
    icon_cloud(d, cx-int(r*0.08), cy+int(r*0.14), int(r*0.66))

def icon_rain(d, cx, cy, r):
    icon_cloud(d, cx, cy-int(r*0.18), int(r*0.64))
    drop = (100, 170, 255)
    lw = max(2, r//14)
    for dx in [-int(r*0.28), 0, int(r*0.28)]:
        x0 = cx + dx
        y0 = cy + int(r*0.28)
        d.line([(x0,y0),(x0-int(r*0.1),y0+int(r*0.38))], fill=drop, width=lw)

def icon_rain_sun(d, cx, cy, r):
    icon_sun(d, cx+int(r*0.30), cy-int(r*0.28), int(r*0.48))
    icon_rain(d, cx-int(r*0.08), cy+int(r*0.12), int(r*0.70))

def icon_thunder(d, cx, cy, r):
    icon_cloud(d, cx, cy-int(r*0.18), int(r*0.60), color=(120,120,140))
    pts = [
        (cx+int(r*0.08), cy+int(r*0.15)),
        (cx-int(r*0.18), cy+int(r*0.45)),
        (cx+int(r*0.03), cy+int(r*0.45)),
        (cx-int(r*0.14), cy+int(r*0.82)),
        (cx+int(r*0.28), cy+int(r*0.38)),
        (cx+int(r*0.07), cy+int(r*0.38)),
    ]
    d.polygon(pts, fill=C_GOLD)

def icon_snow(d, cx, cy, r):
    lw = max(2, r//12)
    for a in range(0, 180, 60):
        rad = math.radians(a)
        dx2, dy2 = int(r*0.80*math.cos(rad)), int(r*0.80*math.sin(rad))
        d.line([(cx-dx2,cy-dy2),(cx+dx2,cy+dy2)], fill=(200,230,255), width=lw)
    d.ellipse([cx-r//7,cy-r//7,cx+r//7,cy+r//7], fill=(220,240,255))

def icon_fog(d, cx, cy, r):
    lw = max(2, r//12)
    for dy in [-int(r*0.28), 0, int(r*0.28)]:
        d.line([(cx-int(r*0.75),cy+dy),(cx+int(r*0.75),cy+dy)], fill=C_GRAY, width=lw)

ICON_FN = {
    "01d": icon_sun, "01n": lambda d,x,y,r: icon_moon_crescent(d,x,y,r),
    "02d": icon_partly, "02n": icon_partly,
    "03d": icon_cloud, "03n": icon_cloud,
    "04d": lambda d,x,y,r: icon_cloud(d,x,y,r,color=C_GRAY),
    "04n": lambda d,x,y,r: icon_cloud(d,x,y,r,color=C_GRAY),
    "09d": icon_rain, "09n": icon_rain,
    "10d": icon_rain_sun, "10n": icon_rain,
    "11d": icon_thunder, "11n": icon_thunder,
    "13d": icon_snow, "13n": icon_snow,
    "50d": icon_fog, "50n": icon_fog,
}

def draw_icon(d, cx, cy, r, code):
    ICON_FN.get(code, icon_sun)(d, cx, cy, r)


# ─────────────────────────────────────────────
#  Moon phase
# ─────────────────────────────────────────────
MOON_NAMES = ["Новолуние","Молодая луна","Первая четверть",
              "Прибывающая","Полнолуние","Убывающая",
              "Последняя четверть","Старая луна"]

def moon_phase(date):
    known = datetime(2000, 1, 6)
    days = (date - known).days % 29.53058867
    idx = int(days / 29.53058867 * 8) % 8
    return idx, MOON_NAMES[idx]

def draw_moon_glyph(d, cx, cy, r, idx):
    bg = C_BG_TOP
    if idx == 0:
        d.ellipse([cx-r,cy-r,cx+r,cy+r], outline=C_GRAY, width=2)
    elif idx == 4:
        d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=C_GOLD)
    elif idx in (1,2,3):
        d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=C_GOLD)
        cov = int(r*2*(1 - idx/4.0))
        d.ellipse([cx-r,cy-r,cx-r+cov,cy+r], fill=bg)
    else:
        d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=C_GOLD)
        cov = int(r*2*((idx-4)/4.0))
        d.ellipse([cx+r-cov,cy-r,cx+r,cy+r], fill=bg)


# ─────────────────────────────────────────────
#  Temperature sparkline
# ─────────────────────────────────────────────
def draw_sparkline(d, x, y, w, h, forecast):
    n = min(len(forecast), 7)
    if n < 2:
        return
    highs = [forecast[i][1]['max_temp'] for i in range(n)]
    lows  = [forecast[i][1]['min_temp'] for i in range(n)]
    tmin  = min(lows) - 1
    tmax  = max(highs) + 1
    rng   = tmax - tmin or 1

    def tx(i): return int(x + i * w / (n-1))
    def ty(t): return int(y + h - (t-tmin)/rng*h)

    poly = [(tx(i), ty(highs[i])) for i in range(n)]
    poly += [(tx(i), ty(lows[i])) for i in range(n-1,-1,-1)]
    d.polygon(poly, fill=(43,169,139,50))

    sf = fnt(19)
    for i in range(n-1):
        d.line([(tx(i),ty(highs[i])),(tx(i+1),ty(highs[i+1]))], fill=(255,165,60), width=3)
        d.line([(tx(i),ty(lows[i])),(tx(i+1),ty(lows[i+1]))],  fill=(100,195,255), width=3)

    for i in range(n):
        hx,hy = tx(i),ty(highs[i])
        lx,ly = tx(i),ty(lows[i])
        d.ellipse([hx-5,hy-5,hx+5,hy+5], fill=(255,165,60))
        d.ellipse([lx-4,ly-4,lx+4,ly+4], fill=(100,195,255))
        hl = f"{highs[i]:.0f}\u00b0"
        ll = f"{lows[i]:.0f}\u00b0"
        bb = d.textbbox((0,0), hl, font=sf)
        tw = bb[2]-bb[0]
        d.text((hx-tw//2, hy-23), hl, font=sf, fill=(255,210,80))
        bb = d.textbbox((0,0), ll, font=sf)
        tw = bb[2]-bb[0]
        d.text((lx-tw//2, ly+7),  ll,  font=sf, fill=(150,220,255))


# ─────────────────────────────────────────────
#  Localisation
# ─────────────────────────────────────────────
MONTHS     = ['Январь','Февраль','Март','Апрель','Май','Июнь',
              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
DAYS_FULL  = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']
DAYS_SHORT = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']

DESC_MAP = {
    "01d":"Ясно","01n":"Ясно","02d":"Переменно","02n":"Переменно",
    "03d":"Облачно","03n":"Облачно","04d":"Пасмурно","04n":"Пасмурно",
    "09d":"Дождь","09n":"Дождь","10d":"Дождь","10n":"Дождь",
    "11d":"Гроза","11n":"Гроза","13d":"Снег","13n":"Снег",
    "50d":"Туман","50n":"Туман",
}


# ─────────────────────────────────────────────
#  Main class
# ─────────────────────────────────────────────
class LocationStatusImageBuilder:
    W = 1000
    H = 620

    def __init__(self, location, weather_client, dollar_rate=None, euro_rate=None, bitcoin_price=None):
        self.location      = location
        self.wc            = weather_client
        self.dollar_rate   = dollar_rate
        self.euro_rate     = euro_rate
        self.bitcoin_price = bitcoin_price

    # ── public ──────────────────────────────
    def build(self, target_path):
        now = datetime.now()

        from HebrewCalendar import HebrewCalendar
        heb = HebrewCalendar().get_hebrew_date_short_ru()

        _loc, cur_temp, sunrise, sunset = self.wc.get_weather(self.location)
        forecast  = self.wc.get_forecast(self.location)
        cur_icon  = forecast[0][1].get('icon','01d') if forecast else '01d'
        pidx, pname = moon_phase(now)

        img = gradient_bg(self.W, self.H)

        ov  = Image.new('RGBA', (self.W, self.H), (0,0,0,0))
        dov = ImageDraw.Draw(ov)
        for i in range(-self.H, self.W+self.H, 32):
            dov.line([(i,0),(i+self.H,self.H)], fill=(255,255,255,6), width=1)
        img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')

        d = ImageDraw.Draw(img, 'RGBA')
        d.rectangle([(0,0),(self.W,5)], fill=C_TEAL)

        self._left(d, now, heb, sunrise, sunset, pidx, pname)
        self._weather_card(d, cur_temp, cur_icon)
        self._rates_pills(d)
        self._forecast_panel(d, forecast)
        self._footer(d, now)

        img.save(target_path, quality=95)

    # ── left column ─────────────────────────
    def _left(self, d, now, heb, sunrise, sunset, pidx, pname):
        # City name
        d.text((30, 16), "Модиин", font=fnt(50), fill=C_TEAL_LT)

        # Date
        date_str = f"{DAYS_FULL[now.weekday()]}, {now.day} {MONTHS[now.month-1]} {now.year}"
        d.text((30, 76), date_str, font=fnt(26), fill=C_CREAM)

        # Hebrew date
        d.text((30, 112), f"  {heb}", font=fnt(22, bold=False), fill=C_GOLD)

        d.line([(30,146),(500,146)], fill=C_TEAL, width=1)

        # Sunrise
        icon_sun(d, 52, 172, 20)
        d.text((80, 160), f"Восход  {sunrise}", font=fnt(24), fill=C_GOLD)

        # Sunset
        icon_moon_crescent(d, 52, 212, 18, color=(180,205,255), bg=C_BG_TOP)
        d.text((80, 200), f"Закат    {sunset}", font=fnt(24), fill=C_BLUE_LT)

        # Moon phase
        draw_moon_glyph(d, 52, 250, 15, pidx)
        d.text((76, 238), pname, font=fnt(21, bold=False), fill=(185,210,240))



    # ── currency pills (below weather card) ──
    def _rates_pills(self, d):
        # Weather card: cx=640, cy=16, height=278 → bottom at 294
        cy = 300   # just below weather card
        pill_h = 38
        pill_gap = 12
        f = fnt(22)

        # Fiat pills: $1 and €1
        pills = []
        if self.dollar_rate is not None:
            pills.append(("$1", f"{self.dollar_rate:.2f} \u20aa", C_GOLD))
        if self.euro_rate is not None:
            pills.append(("\u20ac1", f"{self.euro_rate:.2f} \u20aa", (160, 210, 255)))

        pill_w = 155
        total_w = len(pills) * pill_w + (len(pills)-1) * pill_gap
        # right-align to match weather card right edge (640+345=985)
        start_x = 985 - total_w

        for i, (symbol, value, color) in enumerate(pills):
            px = start_x + i * (pill_w + pill_gap)
            d.rounded_rectangle([px, cy, px+pill_w, cy+pill_h], radius=19,
                                 fill=(0,0,0,65), outline=color, width=1)
            d.text((px+14, cy+8), symbol, font=f, fill=color)
            bb = d.textbbox((0,0), value, font=f)
            tw = bb[2]-bb[0]
            d.text((px+pill_w-tw-12, cy+8), value, font=f, fill=C_CREAM)

        # Bitcoin pill (wider, full width, second row)
        if self.bitcoin_price is not None:
            btc_color = (255, 165, 50)   # orange
            bcy = cy + pill_h + 8
            # format: $92,345
            if self.bitcoin_price >= 1000:
                btc_str = f"${self.bitcoin_price:,.0f}"
            else:
                btc_str = f"${self.bitcoin_price:.0f}"
            btc_pill_w = total_w  # same total width as fiat pills
            bpx = 985 - btc_pill_w
            d.rounded_rectangle([bpx, bcy, bpx+btc_pill_w, bcy+pill_h], radius=19,
                                 fill=(0,0,0,65), outline=btc_color, width=1)
            fb = fnt(20)
            label = "BTC"
            d.text((bpx+14, bcy+9), label, font=fb, fill=btc_color)
            bb = d.textbbox((0,0), btc_str, font=fb)
            tw = bb[2]-bb[0]
            d.text((bpx+btc_pill_w-tw-12, bcy+9), btc_str, font=fb, fill=C_CREAM)

    # ── weather card (right) ─────────────────
    def _weather_card(self, d, cur_temp, cur_icon):
        cx, cy, cw, ch = 640, 16, 345, 278
        d.rounded_rectangle([cx,cy,cx+cw,cy+ch], radius=20,
                             fill=(0,0,0,75), outline=C_TEAL, width=1)

        # icon left side
        draw_icon(d, cx+82, cy+108, 76, cur_icon)

        # temperature right side
        d.text((cx+170, cy+28), f"{cur_temp:.0f}\u00b0", font=fnt(100), fill=C_WHITE)

        # description below icon
        desc = DESC_MAP.get(cur_icon, "")
        text_center(d, cx+82, cy+200, desc, fnt(22, bold=False), C_GRAY)

    # ── forecast panel (bottom) ──────────────
    def _forecast_panel(self, d, forecast):
        W, H = self.W, self.H
        n = min(len(forecast), 7)
        if n == 0:
            return

        py, ph = 400, H - 400 - 52
        d.rounded_rectangle([18,py,W-18,py+ph], radius=14,
                             fill=(0,0,0,55), outline=(255,255,255,25), width=1)

        d.text((32, py+8), "ПРОГНОЗ НА НЕДЕЛЮ", font=fnt(18, bold=False), fill=C_TEAL_LT)

        col_w = (W-40)//n
        f_day = fnt(21)
        for i, (fdate, _) in enumerate(forecast[:n]):
            cx2 = 20 + i*col_w + col_w//2
            label = DAYS_SHORT[fdate.weekday()]
            color = C_GOLD if fdate.weekday() == 4 else C_CREAM
            text_center(d, cx2, py+32, label, f_day, color)
            if i > 0:
                d.line([(20+i*col_w,py+6),(20+i*col_w,py+ph-6)],
                       fill=(255,255,255,20), width=1)

        margin = 20
        draw_sparkline(d, 20+margin, py+60, W-40-margin*2, ph-78, forecast[:n])

    # ── footer ───────────────────────────────
    def _footer(self, d, now):
        W, H = self.W, self.H
        d.rectangle([(0,H-50),(W,H)], fill=C_BG_BOT)
        d.line([(0,H-50),(W,H-50)], fill=C_TEAL, width=2)
        d.text((28, H-37), "t.me/modiin_ru", font=fnt(24), fill=C_TEAL_LT)
        ts = now.strftime("%H:%M")
        bb = d.textbbox((0,0), ts, font=fnt(20, bold=False))
        tw = bb[2]-bb[0]
        d.text((W-tw-28, H-35), ts, font=fnt(20, bold=False), fill=C_GRAY)