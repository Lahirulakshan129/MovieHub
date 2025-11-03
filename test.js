const axios = require('axios');
const cheerio = require('cheerio');
const pLimit = require('p-limit');
const fs = require('fs');
const { URL } = require('url');

const START_URL = 'https://rargb.to/movies/';
const CONCURRENCY = 6;
const WAIT_BETWEEN_REQUESTS_MS = 350;

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }
function resolveUrl(base, href){ try{ return new URL(href, base).toString(); }catch(e){ return href; } }

async function fetchHtml(url){
  const res = await axios.get(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36',
      Referer: START_URL
    },
    timeout: 20000
  });
  return res.data;
}

function parseListing(html, base){
  const $ = cheerio.load(html);
  const links = [];
  $('a').each((i, el) => {
    const href = $(el).attr('href') || '';
    if(/\/torrent\/.*\.html$/i.test(href) || /\/torrent\//i.test(href)){
      const text = $(el).text().trim();
      if(text && text.length>3){
        links.push(resolveUrl(base, href));
      }
    }
  });
  return Array.from(new Set(links));
}

function parseDetail(html, base){
  const $ = cheerio.load(html);
  const result = {};
  const h1 = $('h1.black').first().text().trim() || $('title').text().trim();
  result.title = h1;
  const posterEl = $('img[src*="/static/movie/"]').first();
  const poster = posterEl.attr('src') ? resolveUrl(base, posterEl.attr('src')) : null;
  result.poster = poster;
  const magnetEl = $('a[href^="magnet:"]').first();
  result.magnet = magnetEl.attr('href') || null;
  const screenshots = [];
  $('#description img, .descrimg, img.img-responsive').each((i, el) => {
    const s = $(el).attr('src');
    if(s) screenshots.push(resolveUrl(base, s));
  });
  result.screenshots = screenshots;
  const added = $('td.lista:contains("Added:")').next().text().trim() || $('tr:contains("Added:") td.lista').text().trim();
  result.added = added || (() => {
    const t = $('td').filter((i,el)=>$(el).prev().text().includes('Added')).text().trim();
    return t || null;
  })();
  const size = $('td.lista:contains("Size:")').next().text().trim() || $('tr:contains("Size:") td.lista').text().trim();
  result.size = size || null;
  const peersText = $('tr:contains("Peers:")').text() || $('td:contains("Seeders")').text();
  result.peers = peersText.replace(/\s+/g,' ').trim() || null;
  const descHtml = $('#description').html() || null;
  result.description_html = descHtml ? descHtml.trim() : null;
  return result;
}

(async ()=>{
  try{
    const listingHtml = await fetchHtml(START_URL);
    const detailLinks = parseListing(listingHtml, START_URL).filter(u=>u.includes('/torrent/'));
    const limit = pLimit(CONCURRENCY);
    const items = [];
    for(let i=0;i<detailLinks.length;i++){
      const url = detailLinks[i];
      await sleep(WAIT_BETWEEN_REQUESTS_MS);
      items.push(limit(async ()=>{
        try{
          const html = await fetchHtml(url);
          const parsed = parseDetail(html, url);
          parsed.url = url;
          console.log('fetched:', parsed.title || url);
          return parsed;
        }catch(err){
          console.error('skip', url, err.message);
          return null;
        }
      }));
    }
    const results = (await Promise.all(items)).filter(Boolean);
    fs.writeFileSync('movies.json', JSON.stringify(results, null, 2), 'utf8');
    const rows = results.map(m=>{
      const img = m.poster? `<img src="${m.poster}" style="width:140px;height:auto;display:block;margin-bottom:6px">` : '';
      const screenshots = (m.screenshots||[]).map(s=>`<a href="${s}" target="_blank">s</a>`).join(' ');
      const magnetBtn = m.magnet ? `<a href="${m.magnet}">Magnet</a>` : '';
      return `<div style="width:220px;padding:8px;margin:8px;border:1px solid #ddd;border-radius:8px">
        ${img}
        <div style="font-weight:600">${m.title||''}</div>
        <div style="font-size:12px">${m.size||''} ${m.added?'<br>'+m.added:''}</div>
        <div style="margin-top:6px">${magnetBtn}</div>
      </div>`;
    }).join('\n');
    const htmlPage = `<!doctype html>
<html><head><meta charset="utf-8"><title>RARGB Movies with Posters</title></head>
<body style="font-family:Arial,Helvetica,sans-serif">
<h1>Movies</h1>
<div style="display:flex;flex-wrap:wrap">${rows}</div>
</body></html>`;
    fs.writeFileSync('movies_with_posters.html', htmlPage, 'utf8');
    console.log('done. saved movies.json and movies_with_posters.html');
  }catch(e){
    console.error(e);
    process.exit(1);
  }
})();
