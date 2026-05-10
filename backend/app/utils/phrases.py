"""
Static phrase cache for standard, non-dynamic messages.
Tone guidelines:
- English (en): Direct plain language, no jargon.
- Yoruba (yo): Respectful honorifics, warm elder-to-community tone.
- Igbo (ig): Progress-oriented, growth-centric (Oganiru).
- Hausa (ha): Community and trust language.
- Pidgin (pcm): Casual friendly energy.
"""

PHRASES = {
    "greeting": {
        "en": "Welcome to AAJE — your Digital Business Manager. How can I help you today?",
        "yo": "Ẹ káàbọ̀ sí AAJE — Olùṣàkóso Ìṣòwò rẹ. Báwo ni mo ṣe le ràn yín lọ́wọ́ lónìí?",
        "ig": "Nnọọ na AAJE — Onye Nlekọta Azụmahịa gị. Kedu ka m ga-esi nyere gị aka maka ọganiru azụmahịa gị taa?",
        "ha": "Barka da zuwa AAJE — Manajan Kasuwancin ku. Yaya zan taimaka muku yau don samun albarka?",
        "pcm": "Welcome to AAJE! How far? Wetin you need make we do today?",
    },
    "pin_request": {
        "en": "Please enter your 4-digit PIN to confirm.",
        "yo": "Ẹ jọ̀wọ́, ẹ tẹ nọ́ńbà ìkọkọ̀ ẹlẹ́yọ mẹ́rin (PIN) yín láti fìdí rẹ̀ múlẹ̀.",
        "ig": "Biko tinye koodu PIN nwere ọnụọgụ anọ gị iji kwado.",
        "ha": "Don Allah shigar da lambar sirri (PIN) mai lamba hudu don tabbatarwa.",
        "pcm": "Abeg put your 4-digit PIN so we go run am.",
    },
    "pin_wrong": {
        "en": "Wrong PIN. Please try again.",
        "yo": "Nọ́ńbà ìkọkọ̀ náà kò tọ̀nà. Ẹ jọ̀wọ́, ẹ tún gbìyànjú.",
        "ig": "PIN ezighi ezi. Biko nwaa ọzọ maka ọganiru.",
        "ha": "Lambar sirri ba daidai ba ce. Don Allah a sake gwadawa.",
        "pcm": "You put wrong PIN. Abeg try am again.",
    },
    "pin_locked": {
        "en": "Too many wrong attempts. Your account is temporarily locked.",
        "yo": "Ẹ ti gbìyànjú jù. Àkọ́ọ́ǹtì yín ti wà ní títìpa fún ìgbà díẹ̀ láti dáàbò bò yín.",
        "ig": "Ị nwaala ọtụtụ ugboro. E mechiela akaụntụ gị nwa oge iji chekwaa gị.",
        "ha": "Kun yi ƙoƙari da yawa. An rufe asusunku na ɗan lokaci don tsaro.",
        "pcm": "You don try too many times. We don lock your account for now to protect your money.",
    },
    "pin_confirmed": {
        "en": "PIN confirmed successfully.",
        "yo": "A ti fìdí nọ́ńbà ìkọkọ̀ yín múlẹ̀ ní ìrọ̀rùn.",
        "ig": "Anabatala PIN gị nke ọma maka ọganiru gị.",
        "ha": "An tabbatar da lambar sirri yadda ya kamata.",
        "pcm": "Your PIN correct! We move.",
    },
    "identity_confirmed": {
        "en": "Identity confirmed successfully.",
        "yo": "A ti fìdí ẹni tí ẹ jẹ́ múlẹ̀, ẹ kú iṣẹ́.",
        "ig": "Anabatala njirimara gị nke ọma. Anyị na-aga n'ihu maka ọganiru.",
        "ha": "An tabbatar da ko kai waye cikin nasara da amana.",
        "pcm": "We don confirm say na you. We dey together.",
    },
    "identity_failed": {
        "en": "Identity verification failed. Please try again.",
        "yo": "A kò rí ẹ̀rí láti fìdí ẹni tí ẹ jẹ́ múlẹ̀. Ẹ jọ̀wọ́, ẹ tún gbìyànjú.",
        "ig": "Nnwale njirimara adaala. Biko nwaa ọzọ.",
        "ha": "Ba a sami nasarar tantancewa ba. Don Allah a sake gwadawa.",
        "pcm": "We no fit confirm your identity. Abeg try am again.",
    },
    "account_linking": {
        "en": "Please link your bank account to continue.",
        "yo": "Ẹ jọ̀wọ́, ẹ so àkọ́ọ́ǹtì ilé-ìfowópamọ́ yín pọ̀ kí a lè tẹ̀síwájú.",
        "ig": "Biko jikọọ akaụntụ ụlọ akụ gị ka anyị gaa n'ihu maka ọganiru.",
        "ha": "Don Allah hada asusun bankinku don mu ci gaba da kasuwanci.",
        "pcm": "Abeg link your bank account so we go fit continue.",
    },
    "account_linked": {
        "en": "Your bank account has been linked successfully.",
        "yo": "A ti so àkọ́ọ́ǹtì ilé-ìfowópamọ́ yín pọ̀ láìsí wàhálà.",
        "ig": "Ejikọla akaụntụ ụlọ akụ gị nke ọma. Ọganiru abịala.",
        "ha": "An haɗa asusun bankinku cikin nasara da amana.",
        "pcm": "We don link your bank account! Better days.",
    },
    "processing": {
        "en": "Processing your request, please wait.",
        "yo": "A ń ṣiṣẹ́ lórí ìbéèrè yín, ẹ jọ̀wọ́ ẹ mú sùúrù.",
        "ig": "Anyị na-ahazi arịrịọ gị, biko chere obere.",
        "ha": "Muna aiki kan buƙatarku, don Allah ku jira kaɗan.",
        "pcm": "We dey process am, abeg hold on small.",
    },
    "withdrawal_confirmed": {
        "en": "Your withdrawal has been processed successfully.",
        "yo": "A ti gbé owó tí ẹ fẹ́ yọ jáde fún yín. Ẹ kú iṣẹ́ ajé.",
        "ig": "E meela ndọrọ ego gị nke ọma. Jisie ike n'ahịa gị.",
        "ha": "An fitar da kuɗinku cikin nasara. Allah ya ba da sa'a.",
        "pcm": "Your withdrawal don enter! Go flex.",
    },
    "payment_confirmed": {
        "en": "Payment has been processed successfully.",
        "yo": "A ti ṣe ìsanwó yín láìsí ìdíwọ́. Ọlọ́run á pèsè púpọ̀ síi.",
        "ig": "E meela ịkwụ ụgwọ gị nke ọma. Ọganiru ka dị n'ihu.",
        "ha": "An biya kuɗin cikin nasara da amana.",
        "pcm": "Payment don drop successfully. No wahala.",
    },
    "error_generic": {
        "en": "An error occurred. Please try again later.",
        "yo": "Àṣìṣe kan wáyé. Ẹ jọ̀wọ́, ẹ tún gbìyànjú nígbà míràn.",
        "ig": "Enwere nsogbu. Biko nwaa ọzọ ma emechaa.",
        "ha": "An sami matsala. Don Allah a sake gwadawa anjima.",
        "pcm": "Small network issue dey. Abeg try am later.",
    },
    "help_menu": {
        "en": "Here is the help menu. Reply with what you need.",
        "yo": "Èyí ni àkójọ ìrànlọ́wọ́. Ẹ jọ̀wọ́, ẹ sọ ohun tí ẹ nílò.",
        "ig": "Nke a bụ ndepụta enyemaka. Gwa anyị ihe ịchọrọ maka ọganiru gị.",
        "ha": "Ga tsarin neman taimako. Ku faɗi abin da kuke buƙata don mu taimaka.",
        "pcm": "See help menu here. Tell us wetin you need make we run am.",
    }
}

def get_phrase(phrase_key: str, language_code: str = "en") -> str:
    """
    Returns the static phrase for the given key and language code.
    Falls back to English if the language is not found.
    If the phrase key doesn't exist, returns a generic error string in the requested language.
    """
    lang = language_code.lower()
    
    if phrase_key not in PHRASES:
        return PHRASES["error_generic"].get(lang, PHRASES["error_generic"]["en"])
    
    phrase_dict = PHRASES[phrase_key]
    return phrase_dict.get(lang, phrase_dict.get("en", "An error occurred."))
