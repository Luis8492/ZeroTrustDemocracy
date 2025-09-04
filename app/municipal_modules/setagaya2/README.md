世田谷区議会の定例会議事録を扱うモジュールです。

# 議事録のパターン
## Pattern1. ネスト型（外側li＋内側ul/li）
概要: `<li>でTopic、その内部に<ul>を置き、<li><strong>質問…</strong></li>と<li><strong>（答弁／役職）…</strong></li>が並ぶ二段構造。`

例: SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_9739_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_9740_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_9747_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_9748_html.html など

## Pattern2. 単一li＋強調タグ連結型
概要: `<li><strong>Topic<br>質問</strong>本文<br><strong>（答弁／役職）…</strong>回答</li> のように、冒頭の<strong>が「Topic＋質問」までを抱え込む。`

例: SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_11415_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_11416_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_16052_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_16053_html.html

## Pattern3. 単一li＋強調タグ分離型
概要: `<li><strong>Topic</strong><br><strong>質問</strong>本文<br><strong>（答弁／役職）</strong>回答</li> と、Topic・質問・回答それぞれが独立した<strong>タグでマークされる。`

例: SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_20655_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_20656_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_21941_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_21942_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_24848_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_24849_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_26569_html.html
SetagayaRegularFetcher_https_www_city_setagaya_lg_jp_02030_26571_html.html など
