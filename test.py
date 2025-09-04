from app.municipal_modules.setagaya2.parsers.setagaya2_parser import Setagaya2Parser
import sys

fileid = sys.argv[1]

p = Setagaya2Parser()
with open('app/raw_minutes/SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_'+fileid+'_html.html','r') as f:
	txt = f.read()
	p.extract_meeting_data(txt)
	man_section = p.extract_questioner_section(txt)[0]
	topic_section = p.extract_topic_section(man_section)
	print(topic_section)
