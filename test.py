from app.municipal_modules.setagaya.regular.parsers.setagaya_regular_parser import (
    SetagayaRegularParser,
)
import sys

fileid = sys.argv[1]

p = SetagayaRegularParser()
with open('app/raw_minutes/SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_'+fileid+'_html.html','r', encoding='utf-8') as f:
	txt = f.read()
	print(p.convert(txt))
