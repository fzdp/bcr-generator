from enum import Enum, unique


@unique
class CSVSource(Enum):
    WORLD_BANK = 1
    OUR_WORLD_IN_DATA = 2
    STATS_GOV = 3
    BGS_MINERALS = 4
    NO_NEED_PREPROCESS = 5
    UN_DATA = 6


@unique
class ChartCategoryIconPosition(Enum):
    LEFT = 1
    RIGHT = 2
    HIDE = 3


@unique
class CategoryLabelPosition(Enum):
    LEFT = 1
    RIGHT = 2


@unique
class BarColorType(Enum):
    COUNTRY_COLOR = 1
    RANDOM_COLOR = 2
    SINGLE_COLOR = 3


@unique
class StatisticsTime(Enum):
    START_OF_THE_YEAR = 1
    END_OF_THE_YEAR = 2


@unique
class ChartType(Enum):
    H_BAR = 1
    V_BAR = 2
    GRID = 3
    GRID_AND_BAR = 4
    LINE_CHART = 5


@unique
class ProvinceNameType(Enum):
    # 北京市 ==> 北京市
    NORMAL = 1
    # 北京市 ==> 北京
    ABBR = 2
    # 北京市 ==> 京
    SINGLE_WORD = 3


# 处理world bank csv
WORLD_BANK_ROWS_TO_DELETE = [
    "Country Code",
    "Indicator Name",
    "Indicator Code",
    # todo 删除一行，只要包含Unnamed字段即可
    "Unnamed: 65",
]

WORLD_BANK_COLUMNS_TO_DELETE = [
    '东亚与太平洋地区（不包括高收入）', '最不发达国家：联合国分类',
    '撒哈拉以南非洲地区', '中东与北非地区',
    '只有IDA', '东亚与太平洋地区 (IBRD与IDA)',
    'IDA總', '撒哈拉以南非洲地区 (IBRD与IDA)',
    '未分类国家', "中东与北非地区（不包括高收入）",
    "拉丁美洲与加勒比海地区", "早人口紅利",
    "重债穷国 (HIPC)", "脆弱和受衝突影響的情況下",
    '人口紅利之後', '高收入国家', '经合组织成员', '美属萨摩亚',
    '北美', '阿拉伯联盟国家', '中东与北非地区', '中东与北非地区 (IBRD与IDA)',
    "IBRD与IDA", "後期人口紅利",
    "小国", "欧洲联盟",
    "中低等收入国家", "人口紅利之後",
    "欧洲与中亚地区", "欧洲货币联盟",
    "中高等收入国家", "中歐和波羅的海",
    "加勒比小国", "其他小国",
    "拉丁美洲与加勒比海地区 (IBRD与IDA)",
    "中低收入国家", "只有IBRD",
    "預人口紅利", "拉丁美洲与加勒比海地区（不包括高收入）",
    "南亚 (IBRD与IDA)", "撒哈拉以南非洲地区（不包括高收入）",
    "中等收入国家", "欧洲与中亚地区（不包括高收入）",
    "低收入国家", "IDA混合",
    "欧洲与中亚地区 (IBRD与IDA)",
    "东亚与太平洋地区", "约旦河西岸和加沙",
    "南亚",
    # 世界不应该移除，可以添加世界总量指标
    "海峡群岛",
    "世界"
]

COUNTRY_NAME_MAPS = {
    '伊朗伊斯兰共和国': '伊朗',
    '阿拉伯联合酋长国': '阿联酋',
    '阿拉伯叙利亚共和国': '叙利亚',
    '俄罗斯联邦': '俄罗斯',
    '阿拉伯埃及共和国': '埃及',
    '安道尔共和国': '安道尔',
    '大韩民国': '韩国',
    '几内亚比绍共和国': '几内亚比绍',
    "中国香港特别行政区": "中国香港",
    "斯洛伐克共和国": "斯洛伐克",
    "也门共和国": "也门",
    "朝鲜民主主义人民共和国": "朝鲜",
    "中国澳门特别行政区": "中国澳门",
    "捷克共和国": "捷克",
    "委内瑞拉玻利瓦尔共和国": "委内瑞拉",
    "多米尼加共和国": "多米尼加",
    "文莱达鲁萨兰国": "文莱",
    "中非共和国": "中非",
}


PROVINCE_NAME_ABBR_MAPS = {
    "北京市": "北京",
    "天津市": "天津",
    "河北省": "河北",
    "山西省": "山西",
    "内蒙古自治区": "内蒙古",
    "辽宁省": "辽宁",
    "吉林省": "吉林",
    "黑龙江省": "黑龙江",
    "上海市": "上海",
    "江苏省": "江苏",
    "浙江省": "浙江",
    "安徽省": "安徽",
    "福建省": "福建",
    "江西省": "江西",
    "山东省": "山东",
    "河南省": "河南",
    "湖北省": "湖北",
    "湖南省": "湖南",
    "广东省": "广东",
    "广西壮族自治区": "广西",
    "海南省": "海南",
    "重庆市": "重庆",
    "四川省": "四川",
    "贵州省": "贵州",
    "云南省": "云南",
    "西藏自治区": "西藏",
    "陕西省": "陕西",
    "甘肃省": "甘肃",
    "青海省": "青海",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
}

# 如果有多个简称，则依据车牌简称
PROVINCE_NAME_SINGLE_WORD_MAPS = {
    "北京市": "京",
    "天津市": "津",
    "河北省": "冀",
    "山西省": "晋",
    "内蒙古自治区": "蒙",
    "辽宁省": "辽",
    "吉林省": "吉",
    "黑龙江省": "黑",
    "上海市": "沪",
    "江苏省": "苏",
    "浙江省": "浙",
    "安徽省": "皖",
    "福建省": "闽",
    "江西省": "赣",
    "山东省": "鲁",
    "河南省": "豫",
    "湖北省": "鄂",
    "湖南省": "湘",
    "广东省": "粤",
    "广西壮族自治区": "桂",
    "海南省": "琼",
    "重庆市": "渝",
    "四川省": "川",
    "贵州省": "贵",
    "云南省": "云",
    "西藏自治区": "藏",
    "陕西省": "陕",
    "甘肃省": "甘",
    "青海省": "青",
    "宁夏回族自治区": "宁",
    "新疆维吾尔自治区": "新",
}

WORLD_AREAS_TO_DELETE = [
    "High SDI", "High income", "High-middle SDI", "Latin America & Caribbean",
    "Low SDI", "Low income", "Low-middle SDI", "Lower-middle income", "Middle East & North Africa",
    "Middle SDI", "North America", "Northern Mariana Islands", "Oceania",
    "South Asia", "South Sudan", "Southeast Asia","Southeast Asia, East Asia, and Oceania",
    "Southern Sub-Saharan Africa", "Sub-Saharan Africa", "Tropical Latin America",
    "Upper-middle income", "Western Europe", "Western Sub-Saharan Africa",
    "Asia", "Australasia", 'Central Asia', 'Central Europe', 'Central Latin America',
    'Central Sub-Saharan Africa', 'East Asia', 'East Asia & Pacific', 'Eastern Europe', 'Eastern Sub-Saharan Africa',
    'Europe & Central Asia', 'Europe', 'World', 'Africa', "Saint Helena", "Gibraltar", "OECD",
    "Europe (other)", "Faeroe Islands", "Other S. & Cent. America", "Saint Pierre and Miquelon",
    "Middle East", "Falkland Islands", "Other Asia & Pacific", "Asia and Oceania", "Guadeloupe",
    "OPEC", "Central and South America", "CIS", "United States Pacific Islands",
    "Martinique", "South & Central America", "Inde", "New Caledonia", "Other Africa", "Other CIS",
    "Persian Gulf", "United States Virgin Islands", "Western Sahara", "EU-28", "Asia Pacific",
    "Netherlands Antilles", "Reunion", "Eurasia", "Western Asia", "Northern Africa", "Australia & New Zealand",
    '"Asia, Central"', "Asia, Central", "Western Africa", "Caribbean", "Eastern Africa", "Southern Europe", "Small island developing States",
    "Northern Europe", "Belgium-Luxembourg", "Europe, Western", "European Union", "Southern Africa", "Northern America",
    "Western Africa", "Central America", "Western Asia", "Polynesia", "Eastern Asia", "Net Food Importing Developing Countries",
    "Least Developed Countries", "Southern Asia", "South America", "Middle Africa", "Low Income Food Deficit Countries",
    "Land Locked Developing Countries", "South Eastern Asia", "Americas", "Pacific Islands Trust Territory",
    "Micronesia (region)", "Melanesia", "Neth. Antilles (former)", "Yemen, Dem. (former)", "Other Asia",
    "Yemen Arab Rep. (former)", "Eastern and South-Eastern Asia", "Oceania (excluding Australia and New Zealand)",
    "Australia/New Zealand", "Low-income countries", "Least developed countries", "Other non-specified areas",
    "Small Island Developing States (SIDS)", "Land-locked Developing Countries (LLDC)", "Lower-middle-income countries",
    "Europe and Northern America", "Latin America and the Caribbean", "Central and Southern Asia",
    "Less developed regions, excluding least developed countries", "Mayotte", "Upper-middle-income countries",
    "Middle-income countries", "No income group available", "High-income countries", "Less developed regions, excluding China",
    "South-Eastern Asia", "Réunion", "More developed regions", "Less developed regions", "Channel Islands",
    "Northern Africa and Western Asia", "Micronesia (Fed. States of)"
]

COUNTRY_NAME_ENGLISH_TO_CHINESE = {
    "Afghanistan": "阿富汗",
    "Africa": "非洲",
    "Albania": "阿尔巴尼亚",
    "Algeria": "阿尔及利亚",
    "Andorra": "安道尔",
    "Angola": "安哥拉",
    "Antigua and Barbuda": "安提瓜和巴布达",
    "Argentina": "阿根廷",
    "Armenia": "亚美尼亚",
    "Australia": "澳大利亚",
    "Austria": "奥地利",
    "Azerbaijan": "阿塞拜疆",
    "Bahamas": "巴哈马",
    "Bahrain": "巴林",
    "Bangladesh": "孟加拉国",
    "Barbados": "巴巴多斯",
    "Belarus": "白俄罗斯",
    "Belgium": "比利时",
    "Belize": "伯利兹",
    "Benin": "贝宁",
    "Bhutan": "不丹",
    "Bolivia": "玻利维亚",
    "Bolivia (Plurinational State of)": "玻利维亚",
    "Bolivia (Plur. State of)": "玻利维亚",
    "USSR": "苏联",
    "USSR (former)": "苏联",
    "Bosnia and Herzegovina": "波黑",
    "Botswana": "博茨瓦纳",
    "Brazil": "巴西",
    "Brunei": "文莱",
    "Brunei Darussalam": "文莱",
    "Bulgaria": "保加利亚",
    "Burkina Faso": "布基纳法索",
    "Burundi": "布隆迪",
    "Cambodia": "柬埔寨",
    "Cameroon": "喀麦隆",
    "Canada": "加拿大",
    "Cape Verde": "佛得角",
    "Cabo Verde": "佛得角",
    "Central African Republic": "中非",
    "Chad": "乍得",
    "Chile": "智利",
    "China": "中国",
    "China, mainland": "中国大陆",
    "Colombia": "哥伦比亚",
    "Comoros": "科摩罗",
    "Congo": "刚果",
    "Cook Islands": "库克群岛",
    "Costa Rica": "哥斯达黎加",
    "Cote d'Ivoire": "科特迪瓦",
    "Côte d'Ivoire": "科特迪瓦",
    "Ivory Coast": "科特迪瓦",
    "Croatia": "克罗地亚",
    "Cuba": "古巴",
    "Cyprus": "塞浦路斯",
    "Czech Republic": "捷克",
    "Czechia": "捷克",
    "Democratic Republic of Congo": "刚果（金）",
    "Dem. Rep. of the Congo": "刚果（金）",
    "Democratic Republic of the Congo": "刚果（金）",
    "Denmark": "丹麦",
    "Djibouti": "吉布提",
    "Dominica": "多米尼克",
    "Dominican Republic": "多米尼加",
    "Eastern Mediterranean": "东地中海",
    "Ecuador": "厄瓜多尔",
    "Egypt": "埃及",
    "El Salvador": "萨尔瓦多",
    "Equatorial Guinea": "赤道几内亚",
    "Eritrea": "厄立特里亚",
    "Estonia": "爱沙尼亚",
    "Ethiopia": "埃塞俄比亚",
    "Europe": "欧洲",
    "Fiji": "斐济",
    "Finland": "芬兰",
    "France": "法国",
    "Gabon": "加蓬",
    "Gambia": "冈比亚",
    "Georgia": "格鲁吉亚",
    "Germany": "德国",
    "Germany, Fed. R. (former)": "西德",
    "German Dem. R. (former)": "东德",
    "Ghana": "加纳",
    "Global": "世界",
    "Greece": "希腊",
    "Grenada": "格林纳达",
    "Guatemala": "危地马拉",
    "Guinea": "几内亚",
    "Guinea-Bissau": "几内亚比绍",
    "Guyana": "圭亚那",
    "Haiti": "海地",
    "Honduras": "洪都拉斯",
    "Hungary": "匈牙利",
    "Iceland": "冰岛",
    "India": "印度",
    "Indonesia": "印度尼西亚",
    "Iran": "伊朗",
    "Iran (Islamic Republic of)": "伊朗",
    "Iran (Islamic Rep. of)": "伊朗",
    "Iraq": "伊拉克",
    "Ireland": "爱尔兰",
    "Israel": "以色列",
    "Italy": "意大利",
    "Jamaica": "牙买加",
    "Japan": "日本",
    "Jordan": "约旦",
    "Kazakhstan": "哈萨克斯坦",
    "Kenya": "肯尼亚",
    "Kiribati": "基里巴斯",
    "Kuwait": "科威特",
    "Kyrgyzstan": "吉尔吉斯斯坦",
    "Laos": "老挝",
    "Lao People's Democratic Republic": "老挝",
    "Latvia": "拉脱维亚",
    "Lebanon": "黎巴嫩",
    "Lesotho": "莱索托",
    "Liberia": "利比里亚",
    "Libya": "利比亚",
    "Lithuania": "立陶宛",
    "Luxembourg": "卢森堡",
    "Macedonia": "马其顿",
    "Madagascar": "马达加斯加",
    "Malawi": "马拉维",
    "Malaysia": "马来西亚",
    "Maldives": "马尔代夫",
    "Mali": "马里",
    "Malta": "马耳他",
    "Marshall Islands": "马绍尔群岛",
    "Mauritania": "毛里塔尼亚",
    "Mauritius": "毛里求斯",
    "Mexico": "墨西哥",
    "Micronesia (country)": "密克罗尼西亚",
    "Micronesia (Federated States of)": "密克罗尼西亚",
    "Micronesia (Fed. States of)": "密克罗尼西亚",
    "Curaçao": "库拉索",
    "British Virgin Islands": "英属维尔京群岛",
    "Moldova": "摩尔多瓦",
    "Republic of Moldova": "摩尔多瓦",
    "Mongolia": "蒙古",
    "Montenegro": "黑山",
    "Morocco": "摩洛哥",
    "Mozambique": "莫桑比克",
    "Myanmar": "缅甸",
    "Burma": "缅甸",
    "Namibia": "纳米比亚",
    "Nauru": "瑙鲁",
    "Nepal": "尼泊尔",
    "Netherlands": "荷兰",
    "New Zealand": "新西兰",
    "Nicaragua": "尼加拉瓜",
    "Niger": "尼日尔",
    "Nigeria": "尼日利亚",
    "Niue": "纽埃",
    "North Korea": "朝鲜",
    "Democratic People's Republic of Korea": "朝鲜",
    "Korea, Dem.Ppl's.Rep.": "朝鲜",
    "Dem. People's Republic of Korea": "朝鲜",
    "Norway": "挪威",
    "Oman": "阿曼",
    "Pakistan": "巴基斯坦",
    "Palau": "帕劳",
    "Panama": "巴拿马",
    "Papua New Guinea": "巴布亚新几内亚",
    "Paraguay": "巴拉圭",
    "Peru": "秘鲁",
    "Philippines": "菲律宾",
    "Poland": "波兰",
    "Portugal": "葡萄牙",
    "Qatar": "卡塔尔",
    "Romania": "罗马尼亚",
    "Russia": "俄罗斯",
    "Russian Federation": "俄罗斯",
    "Rwanda": "卢旺达",
    "Saint Kitts and Nevis": "圣基茨和尼维斯",
    "Saint Lucia": "圣卢西亚",
    "Saint Vincent and the Grenadines": "圣文森特和格林纳丁斯",
    "Samoa": "萨摩亚",
    "Sao Tome and Principe": "圣多美和普林西比",
    "Saudi Arabia": "沙特阿拉伯",
    "Senegal": "塞内加尔",
    "Serbia": "塞尔维亚",
    "Seychelles": "塞舌尔",
    "Sierra Leone": "塞拉利昂",
    "Singapore": "新加坡",
    "Slovakia": "斯洛伐克",
    "Slovenia": "斯洛文尼亚",
    "Solomon Islands": "所罗门群岛",
    "Somalia": "索马里",
    "South Africa": "南非",
    "South Korea": "韩国",
    "Republic of Korea": "韩国",
    "Korea, Republic of": "韩国",
    "South-East Asia": "东南亚",
    "Spain": "西班牙",
    "Sri Lanka": "斯里兰卡",
    "Sudan (former)": "苏丹",
    "Sudan": "南苏丹",
    "Suriname": "苏里南",
    "Swaziland": "斯威士兰",
    "Sweden": "瑞典",
    "Switzerland": "瑞士",
    "Syria": "叙利亚",
    "Syrian Arab Republic": "叙利亚",
    "Tajikistan": "塔吉克斯坦",
    "Tanzania": "坦桑尼亚",
    "United Rep. of Tanzania": "坦桑尼亚",
    "United Republic of Tanzania": "坦桑尼亚",
    "Thailand": "泰国",
    "Timor": "东帝汶",
    "Timor-Leste": "东帝汶",
    "Togo": "多哥",
    "Tonga": "汤加",
    "Trinidad and Tobago": "特立尼达和多巴哥",
    "Tunisia": "突尼斯",
    "Turkey": "土耳其",
    "Turkmenistan": "土库曼斯坦",
    "Tuvalu": "图瓦卢",
    "Uganda": "乌干达",
    "Ukraine": "乌克兰",
    "United Arab Emirates": "阿联酋",
    "United Kingdom": "英国",
    "United States": "美国",
    "United States of America": "美国",
    "Uruguay": "乌拉圭",
    "Uzbekistan": "乌兹别克斯坦",
    "Vanuatu": "瓦努阿图",
    "Venezuela": "委内瑞拉",
    "Venezuela (Bolivarian Republic of)": "委内瑞拉",
    "Venezuela (Bolivar. Rep.)": "委内瑞拉",
    "Vietnam": "越南",
    "Viet Nam": "越南",
    "Western Pacific": "西太平洋",
    "Yemen": "也门",
    "Zambia": "赞比亚",
    "Zimbabwe": "津巴布韦",
    "American Samoa": "美属萨摩亚",
    "Bermuda": "百慕大",
    "Greenland": "格陵兰",
    "Guam": "关岛",
    "Micronesia": "密克罗尼西亚",
    "Palestine": "巴勒斯坦",
    "State of Palestine": "巴勒斯坦",
    "Puerto Rico": "波多黎各",
    "Taiwan": "中国台湾",
    "China, Taiwan Province of": "中国台湾",
    "Macao": "中国澳门",
    "China, Macao SAR": "中国澳门",
    "Hong Kong": "中国香港",
    "China, Hong Kong SAR": "中国香港",
    "Eswatini": "斯威士兰",
    "Czechoslovakia": "捷克斯洛伐克",
    "Czechoslovakia (former)": "捷克斯洛伐克",
    "Aruba": "阿鲁巴",
    "French Polynesia": "法属波利尼西亚",
    "Turks and Caicos Islands": "特克斯和凯科斯群岛",
    "French Guiana": "法属圭亚那",
    "Montserrat": "蒙特塞拉特",
    "Yugoslavia": "南斯拉夫",
    "Yugoslavia, SFR (former)": "南斯拉夫",
    "Cayman Islands": "开曼群岛",
    "Kosovo": "科索沃",
    "Melanesia": "美拉尼西亚",
    "North Macedonia": "北马其顿",
    "Serbia and Montenegro": "塞黑",
    "Ethiopia PDR": "埃塞俄比亚人民民主共和国",
    "Ethiopia, incl. Eritrea": "埃塞俄比亚(含厄立特里亚)",
    "World": "世界"
}

GENERIC_COLORS = [
    "#ffb6c1", "#5aa469", "#8f384d", "#1aa6b7", "#84a9ac",
    "#848ccf", "#0fabbc",
    "#228b22", "#d2691e", "#556b2f", "#a52a2a", "#483d8b",
    "#9400d3", "#00fa9a", "#1e90ff", "#f0e68c", "#dda0dd",
    "#7b68ee", "#ffa07a", "#ee82ee", "#87cefa", "#7fffd4",
    "#008080", "#4682b4", "#9acd32", "#32cd32", "#8b008b",
    "#b03060", "#d2b48c", "#00ced1", "#ffa500", "#ffd700",
]

COUNTRY_COLORS = {
    '中国': "#de2910",
    '美国': "#0c1b9c",
    '印度': "#ff9933",
    '南斯拉夫': '#D60000',
    '尼日利亚': "#008751",
    '印度尼西亚': "#ce1d26",
    '俄罗斯': "#0433ff",
    '巴西': "#01923f",
    '巴基斯坦': "#006600",
    '日本': "#bc1a2d",
    '德国': "#ff2600",
    '墨西哥': "#006847",
    '意大利': "#019246",
    '菲律宾': "#0038a8",
    '埃塞俄比亚': "#f9dd16",
    '英国': "#003399",
    '孟加拉国': "#006a4e",
    '越南': "#ce1d26",
    '法国': "#0155a4",
    '阿联酋': "#009a00",
    "冈比亚": "#0B1679",
    "几内亚比绍": "#FBC711",
    "乌克兰": "#0000C2",
    "希腊": "#00006D",
    "几内亚": "#00824D",
    "赤道几内亚": "#2F8800",
    "津巴布韦": "#FFC800",
    "格陵兰": "#C50B26",
    "危地马拉": "#73BBDC",
    "格林纳达": "#FBC711",
    "巴林": "#C30E1C",
    "关岛": "#003FBC",
    "马恩岛": "#E20E22",
    "加拿大": "#F11E2A",
    "中国澳门": "#00654C",
    "爱尔兰": "#FF6600",
    "瑞典": "#004181",
    "开曼群岛": "#002687",
    "澳大利亚": "#002687",
    "瑞士": "#FF0000",
    "列支敦士登": "#00206C",
    "卢森堡": "#008FD9",
    "丹麦": "#F11E2A",
    "卡塔尔": "#5D132E",
    "沙特阿拉伯": "#008324",
    "巴哈马": "#009BBD",
    "奥地利": "#E91F2B",
    "摩纳哥": "#C30E1C",
    "芬兰": "#002766",
    "冰岛": "#00267B",
    "挪威": "#F11E2A",
    "新加坡": "#E91F2B",
    "科威特": "#008764",
    "圣马力诺": "#006FB6",
    "新西兰": "#002687",
    "百慕大": "#C10000",
    "波兰": "#CA192E",
    "埃及": "#C30E1C",
    "中国香港": "#D61F0E",
    "西班牙": "#FFB700",
    "韩国": "#002765",
    "南非": "#006947",
    "比利时": "#FBD532",
    "马来西亚": "#D4193E",
    "格鲁吉亚": "#FF0000",
    "阿根廷": "#629AD3",
    "图瓦卢": "#629AD3",
    "瑙鲁": "#00206C",
    "马耳他": "#C41020",
    "萨摩亚": "#C30E1C",
    "纽埃": "#FFD900",
    "汤加": "#B40000",
    "库克群岛": "#001B6A",
    "马绍尔群岛": "#002A81",
    "基里巴斯": "#C30E1C",
    "帕劳": "#399DCD",
    "约旦": "#00672E",
    "黎巴嫩": "#58BE86",
    "捷克": "#0E356B",
    "密克罗尼西亚": "#62A3D5",
    "安道尔": "#FBD000",
    "柬埔寨": "#C10000",
    "朝鲜": "#E9161C",
    "老挝": "#001E55",
    "吉尔吉斯斯坦": "#E20E22",
    "乌兹别克斯坦": "#0087A6",
    "阿尔巴尼亚": "#C30E1C",
    "所罗门群岛": "#194926",
    "蒙古": "#379EC4",
    "阿富汗": "#B10000",
    "尼泊尔": "#D4102E",
    "瓦努阿图": "#008333",
    "波黑": "#FFC100",
    "亚美尼亚": "#FF8700",
    "缅甸": "#27A326",
    "塔吉克斯坦": "#005300",
    "东帝汶": "#D41B17",
    "圣多美和普林西比": "#0F9D20",
    "巴布亚新几内亚": "#FBC811",
    "安哥拉": "#C30E1C",
    "阿鲁巴": "#466EAD",
    "刚果（金）": "#006CFF",
    "秘鲁": "#D10F14",
    "安提瓜和巴布达": "#005FBA",
    "哈萨克斯坦": "#009FBE",
    "保加利亚": "#00845B",
    "伊朗": "#1A8E31",
    "罗马尼亚": "#FBC711",
    "土耳其": "#DC0A12",
    "荷兰": "#193678",
    "泰国": "#001B6A",
    "苏联": "#E52822",
    "委内瑞拉": "#00269B",
    "葡萄牙": "#005630",
    "肯尼亚": "#005300",
    "斯里兰卡": "#FFA800",
    "马拉维": "#268C28",
    "莫桑比克": "#FBDA00"
}