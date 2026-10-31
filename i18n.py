"""UI translations. German message templates are stable keys; protocol values stay unchanged."""
import re
LANGUAGES = {'de': 'Deutsch', 'en': 'English', 'zh_CN': '简体中文'}
# German | English | Simplified Chinese
_ROWS = '''Empfang über|Receive via|接收方式
Verbinden|Connect|连接
Trennen|Disconnect|断开
Tabelle leeren|Clear table|清空表格
Getrennt|Disconnected|已断开
Trenne …|Disconnecting …|正在断开…
Verbinde …|Connecting …|正在连接…
Verbindung aktiv|Connection active|连接已启用
Waveshare-IP|Waveshare IP|Waveshare IP
TCP-Port|TCP port|TCP 端口
Kanal|Channel|通道
Bitrate (bit/s)|Bit rate (bit/s)|波特率 (bit/s)
Geräteindex|Device index|设备索引
CAN-Telegramme|CAN frames|CAN 报文
Nutzdaten / Dezimal-Auswertung|Payload / decimal decoding|数据 / 十进制解析
Letzter Empfang|Last received|最近接收
Quelle|Source|来源
CAN-ID Hex|CAN ID hex|CAN ID 十六进制
CAN-ID Dezimal|CAN ID decimal|CAN ID 十进制
Format|Format|格式
Typ|Type|类型
Daten Hex|Data hex|十六进制数据
Bytes Dezimal|Bytes decimal|十进制字节
Anzahl|Count|数量
Rohtelegramm|Raw frame|原始报文
Telegramm auswählen: Byteposition, Hex- und Dezimalwerte werden hier angezeigt.|Select a frame to display byte positions, hex and decimal values here.|选择报文后，此处显示字节位置、十六进制和十进制值。
Auswertung für gewähltes Telegramm anlegen …|Create decoding for selected frame …|为所选报文创建解析…
Feld hinzufügen …|Add field …|添加字段…
Feld bearbeiten …|Edit field …|编辑字段…
Feld entfernen|Remove field|删除字段
Werte als CSV …|Export values as CSV …|导出为 CSV…
Bytepositionen ab 0 · Ergebnis = Rohwert × Faktor ÷ Teiler + Offset · Nur passende CAN-ID und Standard-/Extended-Format werden ausgewertet.|Byte positions start at 0 · Result = raw value × factor ÷ divisor + offset · Only matching CAN IDs and standard/extended formats are decoded.|字节位置从 0 开始 · 结果 = 原始值 × 系数 ÷ 除数 + 偏移量 · 仅解析匹配的 CAN ID 和标准/扩展格式。
Feld|Field|字段
CAN-ID / Format|CAN ID / format|CAN ID / 格式
Bereich|Range|范围
Rohwert dezimal|Raw value decimal|原始值（十进制）
Berechneter Wert|Calculated value|计算值
Einheit|Unit|单位
Empfang|Received|接收时间
Status|Status|状态
Warte auf passenden Frame|Waiting for matching frame|等待匹配的报文
Neues Feld|New field|新字段
CAN-Nutzdaten auswerten|Decode CAN payload|解析 CAN 数据
CAN-ID (0x… = Hex, sonst Dezimal)|CAN ID (0x… = hex, otherwise decimal)|CAN ID（0x… 为十六进制，否则为十进制）
Startbyte (0 bis 7)|Start byte (0 to 7)|起始字节（0 至 7）
Anzahl Bytes (1 bis 8)|Number of bytes (1 to 8)|字节数（1 至 8）
Byte-Reihenfolge|Byte order|字节顺序
Zahlentyp|Number type|数值类型
Bitversatz im Zahlenwert (0 = LSB)|Bit offset in value (0 = LSB)|数值中的位偏移（0 = 最低位）
Bitlänge (0 = verbleibender Bereich)|Bit length (0 = remaining range)|位长度（0 = 剩余范围）
Faktor|Factor|系数
Teiler (Division)|Divisor|除数
Offset|Offset|偏移量
Abbrechen|Cancel|取消
OK|OK|确定
Name|Name|名称
Auswertung prüfen|Check decoding|检查解析设置
Einstellungen|Settings|设置
Eingaben prüfen|Check input|检查输入
Empfang beendet|Reception stopped|接收已停止
Speichern fehlgeschlagen|Save failed|保存失败
Export fehlgeschlagen|Export failed|导出失败
IP/Hostname oder TCP-Port ist ungültig.|Invalid IP/host name or TCP port.|IP 地址、主机名或 TCP 端口无效。
Gegenstelle hat die Verbindung geschlossen.|The remote host closed the connection.|远程主机已关闭连接。
CANalyst verbunden · Nur-Lauschen|CANalyst connected · Listen only|CANalyst 已连接 · 仅监听
LAN verbunden · Nur Empfang|LAN connected · Receive only|LAN 已连接 · 仅接收
keine Nutzdaten|no payload|无数据
Ein Name ist erforderlich.|A name is required.|必须填写名称。
CAN-ID passt nicht zum gewählten Format.|CAN ID does not match the selected format.|CAN ID 与所选格式不匹配。
Bytebereich muss innerhalb von Byte 0 bis 7 liegen.|Byte range must be within bytes 0 to 7.|字节范围必须在 0 至 7 以内。
Unbekanntes Zahlenformat.|Unknown number format.|未知数值格式。
Bitbereich liegt außerhalb des Byteblocks.|Bit range is outside the byte block.|位范围超出字节块。
Float32 benötigt 4, Float64 8 Bytes ohne Bit-Auswahl.|Float32 requires 4 bytes, Float64 8 bytes, without bit selection.|Float32 需要 4 字节，Float64 需要 8 字节，不能选择位。
Faktor, Teiler und Offset müssen endliche Zahlen sein; der Teiler darf nicht 0 sein.|Factor, divisor and offset must be finite numbers; divisor must not be zero.|系数、除数和偏移量必须为有限数；除数不能为 0。
Remote-Frame hat keine Nutzdaten.|Remote frame has no payload.|远程帧没有数据。
DLC zu kurz für diesen Bytebereich.|DLC is too short for this byte range.|DLC 太短，无法读取此字节范围。
Float-Wert ist NaN oder unendlich.|Float value is NaN or infinite.|浮点值为 NaN 或无穷大。
Ergebnis der Skalierung ist zu groß.|Scaled result is too large.|缩放结果过大。
Frames: {count}|Frames: {count}|报文数：{count}
Letzter Frame: {time}|Last frame: {time}|最近报文：{time}
CAN LAN / USB Reader {version} – nur lesend|CAN LAN / USB Reader {version} – read only|CAN LAN / USB Reader {version} – 只读
  CANalyst-II integriert / {bits} Bit · Listen-only|  CANalyst-II built in / {bits} bit · Listen only|  内置 CANalyst-II / {bits} 位 · 仅监听
Log: {path} · Bei jedem Start neu · Auswertungen werden im Benutzerprofil gespeichert.|Log: {path} · Recreated on each start · Decodings are saved in the user profile.|日志：{path} · 每次启动重新创建 · 解析设置保存在用户配置中。
{canid} · Bytes ab 0: {data}|{canid} · Bytes from 0: {data}|{canid} · 字节从 0 开始：{data}
Einstellungen konnten nicht vollständig gelesen werden: {error}|Settings could not be fully read: {error}|无法完整读取设置：{error}
Logdatei kann nicht geschrieben werden: {error}|Cannot write log file: {error}|无法写入日志文件：{error}'''
MESSAGES = {row.split('|')[0]: dict(zip(('en', 'zh_CN'), row.split('|')[1:])) for row in _ROWS.splitlines()}
_HINT = 'Ergebnis = Rohwert × Faktor ÷ Teiler + Offset\nBits: erst Byteblock nach Endian lesen, dann ab LSB zählen.\nKeine DBC-/Motorola-Startbitnummerierung. Float: ganze 4/8 Bytes.'
MESSAGES[_HINT] = {'en': 'Result = raw value × factor ÷ divisor + offset\nBits: read the byte block in endian order, then count from LSB.\nNo DBC/Motorola start-bit numbering. Float: full 4/8 bytes.', 'zh_CN': '结果 = 原始值 × 系数 ÷ 除数 + 偏移量\n位：先按字节顺序读取字节块，再从最低位开始计数。\n不使用 DBC/Motorola 起始位编号。浮点数：完整的 4/8 字节。'}
_PATTERNS = []
for key, values in MESSAGES.items():
    if '{' in key:
        pattern = re.escape(key)
        for name in re.findall(r'\{(\w+)\}', key): pattern = pattern.replace(re.escape('{'+name+'}'), '(?P<'+name+'>.*?)')
        _PATTERNS.append((re.compile('^'+pattern+'$', re.S), values))

def translate(text, language='de'):
    text = str(text)
    if language == 'de' or language not in LANGUAGES: return text
    if text in MESSAGES: return MESSAGES[text][language]
    for pattern, values in _PATTERNS:
        match = pattern.match(text)
        if match: return values[language].format(**{k: translate(v, language) for k,v in match.groupdict().items()})
    return text  # Native OS/driver errors and user data are preserved verbatim.

# Driver errors have the same stable German keys as the transport layer.
MESSAGES.update({
 'Ungültiger CANalyst-Kanal, Geräteindex oder Bitrate.': {'en':'Invalid CANalyst channel, device index or bit rate.', 'zh_CN':'CANalyst 通道、设备索引或波特率无效。'},
 'CANalyst über ControlCAN.dll benötigt Windows.': {'en':'CANalyst via ControlCAN.dll requires Windows.', 'zh_CN':'通过 ControlCAN.dll 使用 CANalyst 需要 Windows。'},
 'Die mitgelieferte CANalyst-Bibliothek fehlt. Bitte den vollständigen Programmordner einschließlich _internal entpacken.': {'en':'The bundled CANalyst library is missing. Extract the entire application folder including _internal.', 'zh_CN':'缺少附带的 CANalyst 库。请解压整个程序文件夹，包括 _internal。'},
 'DLL bietet nicht die erforderliche ControlCAN-Schnittstelle für CANalyst-II.': {'en':'The DLL does not provide the required ControlCAN interface for CANalyst-II.', 'zh_CN':'DLL 未提供 CANalyst-II 所需的 ControlCAN 接口。'},
 'CANalyst-II konnte nicht geöffnet werden. USB-Treiber, Geräteindex und andere laufende CAN-Programme prüfen.': {'en':'Cannot open CANalyst-II. Check the USB driver, device index and other running CAN programs.', 'zh_CN':'无法打开 CANalyst-II。请检查 USB 驱动、设备索引及其他运行中的 CAN 程序。'},
 'Initialisierung im Nur-Lauschen-Modus fehlgeschlagen.': {'en':'Listen-only initialization failed.', 'zh_CN':'仅监听模式初始化失败。'},
 'CANalyst-Empfang konnte nicht gestartet werden.': {'en':'Cannot start CANalyst reception.', 'zh_CN':'无法启动 CANalyst 接收。'},
 'CANalyst ist nicht geöffnet.': {'en':'CANalyst is not open.', 'zh_CN':'CANalyst 未打开。'},
 'CANalyst meldet einen Empfangsfehler; USB-Verbindung und Treiber prüfen.': {'en':'CANalyst reports a receive error; check the USB connection and driver.', 'zh_CN':'CANalyst 报告接收错误；请检查 USB 连接和驱动。'},
 'Ungültige Empfangsanzahl aus der Hersteller-DLL.': {'en':'Invalid receive count from the vendor DLL.', 'zh_CN':'厂商 DLL 返回的接收数量无效。'},
 'Einstellungsdatei enthält kein Objekt.': {'en':'Settings file does not contain an object.', 'zh_CN':'设置文件未包含有效对象。'},
})
