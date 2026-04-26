from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import time

app = Flask(__name__)
CORS(app)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
]

session = requests.Session()

def init_session():
    try:
        session.get("https://www.daraz.com.bd/", headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=10)
    except:
        pass

def parse_sold(sold_str):
    if not sold_str: return 0
    s = str(sold_str).lower().replace(" sold","").replace(",","").strip()
    if "k" in s:
        return int(float(s.replace("k","")) * 1000)
    try: return int(s)
    except: return 0

def fix_image_url(img):
    if not img: return ""
    img = str(img).strip()
    if img.startswith("http"): return img
    elif img.startswith("//"): return "https:" + img
    else: return "https:" + img

def fetch_page(keyword, page, filters):
    time.sleep(random.uniform(0.5, 1.5))
    kw = keyword.replace(" ", "+")
    headers = {
        'Referer': 'https://www.daraz.com.bd/',
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    url = f"https://www.daraz.com.bd/catalog/?ajax=true&page={page}&q={kw}"
    try:
        resp = session.get(url, headers=headers, timeout=15)
        data = resp.json()
        items = data.get('mods', {}).get('listItems', [])
        page_items = []
        for item in items:
            try:
                price = float(item.get('price', 0) or 0)
                rating = float(item.get('ratingScore', 0) or 0)
                sold_num = parse_sold(item.get('itemSoldCntShow'))
                if price < filters['min_price'] or price > filters['max_price']: continue
                if rating < filters['min_rating']: continue
                if sold_num < filters['min_sold']: continue
                page_items.append({
                    'name': item.get('name', 'N/A'),
                    'price': price,
                    'original_price': float(item.get('originalPrice', 0) or 0),
                    'discount': item.get('discount', ''),
                    'rating': rating,
                    'reviews': int(item.get('review', 0) or 0),
                    'sold': item.get('itemSoldCntShow', '0'),
                    'location': item.get('location', 'N/A'),
                    'seller': item.get('sellerName', 'N/A'),
                    'image_url': fix_image_url(item.get('image', '')),
                    'item_url': 'https:' + str(item.get('itemUrl', ''))
                })
            except: continue
        return page_items
    except Exception as e:
        print(f"Error page {page}: {e}")
        return []

HTML_PAGE = """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daraz Finder</title>
<link href="https://fonts.googleapis.com/css2?family=Tiro+Bangla&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--orange:#FF6A00;--dark:#0D0D0D;--dark2:#161616;--dark3:#1E1E1E;--card:#1A1A1A;--border:#2A2A2A;--text:#E8E8E8;--muted:#888;--green:#00D68F;--yellow:#FFD60A;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--dark);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 40% at 20% 10%,rgba(255,106,0,0.08) 0%,transparent 60%);pointer-events:none;z-index:0;}
header{position:relative;z-index:10;padding:1.5rem 1rem 0;max-width:1200px;margin:0 auto;}
.logo{display:flex;align-items:center;gap:10px;margin-bottom:1.5rem;}
.logo-icon{width:38px;height:38px;background:var(--orange);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;}
.logo-text{font-size:1.2rem;font-weight:800;}
.logo-text span{color:var(--orange);}
h1{font-size:clamp(1.6rem,4vw,2.8rem);font-weight:800;line-height:1.15;letter-spacing:-0.5px;margin-bottom:0.4rem;}
h1 .acc{color:var(--orange);}
.sub{color:var(--muted);font-size:0.9rem;margin-bottom:1.5rem;font-family:'Tiro Bangla',serif;}
.search-box{background:var(--dark2);border:1px solid var(--border);border-radius:14px;padding:1.2rem;margin-bottom:1rem;}
.row{display:flex;gap:10px;margin-bottom:1rem;}
input[type=text],input[type=number],select{background:var(--dark3);border:1.5px solid var(--border);border-radius:9px;padding:12px 14px;color:var(--text);font-size:0.9rem;font-family:'Syne',sans-serif;outline:none;transition:border-color .2s;width:100%;}
input:focus,select:focus{border-color:var(--orange);}
input::placeholder{color:var(--muted);}
.btn{background:var(--orange);color:#fff;border:none;border-radius:9px;padding:12px 22px;font-size:0.95rem;font-weight:700;font-family:'Syne',sans-serif;cursor:pointer;white-space:nowrap;transition:.2s;}
.btn:hover{opacity:.9;}
.btn:disabled{opacity:.5;cursor:not-allowed;}
.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;}
.fg label{font-size:0.68rem;color:var(--muted);letter-spacing:.05em;text-transform:uppercase;display:block;margin-bottom:5px;}
.status{max-width:1200px;margin:0 auto .8rem;padding:0 1rem;display:none;}
.status.on{display:block;}
.pill{display:inline-flex;align-items:center;gap:8px;background:var(--dark2);border:1px solid var(--border);border-radius:50px;padding:7px 14px;font-size:.82rem;color:var(--muted);}
.spin{width:13px;height:13px;border:2px solid var(--border);border-top-color:var(--orange);border-radius:50%;animation:spin .7s linear infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
.results{max-width:1200px;margin:0 auto;padding:0 1rem 3rem;position:relative;z-index:5;}
.rh{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;}
.rc{font-size:.82rem;color:var(--muted);}
.rc strong{color:var(--orange);font-size:.95rem;}
.sort{background:var(--dark2);border:1px solid var(--border);border-radius:8px;padding:7px 10px;color:var(--text);font-family:'Syne',sans-serif;font-size:.82rem;outline:none;cursor:pointer;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:13px;overflow:hidden;transition:.2s;animation:up .4s ease both;}
.card:hover{transform:translateY(-3px);border-color:var(--orange);box-shadow:0 8px 25px rgba(255,106,0,.12);}
@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.ci{position:relative;background:#111;height:180px;overflow:hidden;}
.ci img{width:100%;height:100%;object-fit:contain;transition:.3s;}
.card:hover .ci img{transform:scale(1.05);}
.badge{position:absolute;top:8px;left:8px;background:var(--orange);color:#fff;font-size:.68rem;font-weight:700;padding:3px 7px;border-radius:5px;}
.cb{padding:12px;}
.cn{font-size:.82rem;line-height:1.4;color:var(--text);margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-family:'Tiro Bangla',serif;}
.pr{display:flex;align-items:baseline;gap:7px;margin-bottom:8px;}
.pc{font-size:1.05rem;font-weight:800;color:var(--orange);}
.po{font-size:.75rem;color:var(--muted);text-decoration:line-through;}
.cm{display:flex;align-items:center;justify-content:space-between;font-size:.75rem;color:var(--muted);margin-bottom:10px;}
.rt{color:var(--yellow);font-weight:600;}
.sc{color:var(--green);font-weight:600;}
.cf{display:flex;align-items:center;justify-content:space-between;}
.loc{font-size:.68rem;color:var(--muted);}
.vb{background:transparent;border:1.5px solid var(--orange);color:var(--orange);border-radius:7px;padding:5px 12px;font-size:.75rem;font-weight:700;font-family:'Syne',sans-serif;cursor:pointer;text-decoration:none;transition:.2s;}
.vb:hover{background:var(--orange);color:#fff;}
.err{background:rgba(255,50,50,.1);border:1px solid rgba(255,50,50,.3);border-radius:9px;padding:.9rem 1.2rem;color:#ff6b6b;font-size:.85rem;margin-bottom:.8rem;display:none;font-family:'Tiro Bangla',serif;}
.err.on{display:block;}
.empty{text-align:center;padding:3rem 1rem;color:var(--muted);display:none;}
.empty.on{display:block;}
.empty h3{color:var(--text);margin:.5rem 0;}
@media(max-width:500px){.row{flex-direction:column;}.grid{grid-template-columns:repeat(2,1fr);}.ci{height:140px;}}
</style>
</head>
<body>
<header>
  <div class="logo"><div class="logo-icon">🛒</div><div class="logo-text">Daraz <span>Finder</span></div></div>
  <h1>Daraz-এর সেরা পণ্য<br>খুঁজুন <span class="acc">সহজেই</span></h1>
  <p class="sub">কীওয়ার্ড লিখুন, ফিল্টার করুন এবং সেরা দামে পণ্য খুঁজে নিন</p>
  <div class="search-box">
    <div class="row">
      <input type="text" id="q" placeholder="যেমন: watch, toy, phone...">
      <button class="btn" onclick="doSearch()">🔍 খুঁজুন</button>
    </div>
    <div class="filters">
      <div class="fg"><label>সর্বনিম্ন দাম (৳)</label><input type="number" id="minP" placeholder="০"></div>
      <div class="fg"><label>সর্বোচ্চ দাম (৳)</label><input type="number" id="maxP" placeholder="যেকোনো"></div>
      <div class="fg"><label>সর্বনিম্ন রেটিং</label><input type="number" id="minR" placeholder="৪.০" step="0.1" max="5"></div>
      <div class="fg"><label>সর্বনিম্ন বিক্রি</label><input type="number" id="minS" placeholder="১০০"></div>
      <div class="fg"><label>পেজ সংখ্যা</label><input type="number" id="pages" value="3" min="1" max="10"></div>
    </div>
  </div>
</header>

<div class="status" id="sb"><div class="pill"><div class="spin"></div><span>ডেটা লোড হচ্ছে...</span></div></div>

<div class="results">
  <div class="err" id="err"></div>
  <div class="rh" id="rh" style="display:none">
    <div class="rc">মোট <strong id="tc">0</strong> টি পণ্য</div>
    <select class="sort" id="sort" onchange="render()">
      <option value="default">ডিফল্ট</option>
      <option value="price_asc">দাম: কম থেকে বেশি</option>
      <option value="price_desc">দাম: বেশি থেকে কম</option>
      <option value="rating">সেরা রেটিং</option>
      <option value="sold">সেরা বিক্রি</option>
    </select>
  </div>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty"><div style="font-size:2.5rem">🔍</div><h3>কোনো পণ্য পাওয়া যায়নি</h3><p>ফিল্টার পরিবর্তন করে আবার চেষ্টা করুন</p></div>
</div>

<script>
let all=[];
function ps(s){if(!s)return 0;let x=s.toLowerCase().replace(' sold','').replace(',','').trim();if(x.includes('k'))return parseFloat(x)*1000;return parseInt(x)||0;}
async function doSearch(){
  const q=document.getElementById('q').value.trim();
  if(!q){showErr('কীওয়ার্ড দিন!');return;}
  const p=new URLSearchParams({q,pages:document.getElementById('pages').value||3,min_price:document.getElementById('minP').value||0,max_price:document.getElementById('maxP').value||999999,min_rating:document.getElementById('minR').value||0,min_sold:document.getElementById('minS').value||0});
  setLoad(true);hideErr();
  try{
    const r=await fetch('/search?'+p);
    if(!r.ok)throw new Error();
    const d=await r.json();
    all=d.products||[];
    document.getElementById('tc').textContent=all.length;
    document.getElementById('rh').style.display='flex';
    render();
  }catch(e){showErr('❌ সার্ভার error। app.py চালু আছে কিনা দেখুন।');}
  finally{setLoad(false);}
}
function render(){
  const s=document.getElementById('sort').value;
  let p=[...all];
  if(s==='price_asc')p.sort((a,b)=>a.price-b.price);
  else if(s==='price_desc')p.sort((a,b)=>b.price-a.price);
  else if(s==='rating')p.sort((a,b)=>b.rating-a.rating);
  else if(s==='sold')p.sort((a,b)=>ps(b.sold)-ps(a.sold));
  const g=document.getElementById('grid');
  const em=document.getElementById('empty');
  if(!p.length){g.innerHTML='';em.classList.add('on');return;}
  em.classList.remove('on');
  g.innerHTML=p.map((x,i)=>`
  <div class="card" style="animation-delay:${i*.04}s">
    <div class="ci">
      <img src="${x.image_url}" onerror="this.src='https://via.placeholder.com/200x200/1A1A1A/888?text=No+Image'" loading="lazy">
      ${x.discount?`<div class="badge">${x.discount}</div>`:''}
    </div>
    <div class="cb">
      <div class="cn">${x.name}</div>
      <div class="pr"><span class="pc">৳ ${x.price.toLocaleString()}</span>${x.original_price>x.price?`<span class="po">৳ ${x.original_price.toLocaleString()}</span>`:''}</div>
      <div class="cm"><span class="rt">⭐ ${x.rating.toFixed(1)} <span style="color:var(--muted);font-weight:400">(${x.reviews})</span></span><span class="sc">✅ ${x.sold}</span></div>
      <div class="cf"><span class="loc">📍 ${x.location}</span><a href="${x.item_url}" target="_blank" class="vb">দেখুন →</a></div>
    </div>
  </div>`).join('');
}
function setLoad(v){document.querySelector('.btn').disabled=v;document.querySelector('.btn').textContent=v?'⏳ লোড...':'🔍 খুঁজুন';document.getElementById('sb').className='status'+(v?' on':'');}
function showErr(m){const e=document.getElementById('err');e.textContent=m;e.className='err on';}
function hideErr(){document.getElementById('err').className='err';}
document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter')doSearch();});
</script>
</body>
</html>"""

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({'error': 'keyword দিন'}), 400
    pages = min(int(request.args.get('pages', 3)), 10)
    filters = {
        'min_price': float(request.args.get('min_price', 0) or 0),
        'max_price': float(request.args.get('max_price', 999999) or 999999),
        'min_rating': float(request.args.get('min_rating', 0) or 0),
        'min_sold': int(request.args.get('min_sold', 0) or 0),
    }
    all_products = []
    for page in range(1, pages + 1):
        all_products.extend(fetch_page(keyword, page, filters))

    return jsonify({'keyword': keyword, 'total': len(all_products), 'products': all_products})

if __name__ == '__main__':
    print("🚀 Daraz Scraper চালু হচ্ছে...")
    print("🌐 Browser-এ যান: http://127.0.0.1:5000")
    init_session()
    app.run(debug=False, host='127.0.0.1', port=5000)
