from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser
import sys
import json

fileid = sys.argv[1]

p = Setagaya2Parser()
with open('app/raw_minutes/SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_'+fileid+'_html.html','r') as f:
	txt = f.read()
	print(p.convert(txt))
