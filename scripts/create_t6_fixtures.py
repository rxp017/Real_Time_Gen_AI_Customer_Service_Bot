"""Author structured multilingual conversation fixtures; never used by runtime detection."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUESTIONS = {
    "en": {
        "refund": ["What is the refund policy?", "I need a refund please", "Can I get my money back?", "Show me the return rules", "Tell me about bootcamp refunds", "I want refund information", "How do I get a refund?"],
        "delivery_status": ["Where is my order?", "When will my order arrive?", "Please track my order", "I need delivery information", "Show me the shipping details", "My delivery is late", "Can you check when it will be delivered?"],
        "cancel_order": ["Cancel my order please", "I want to cancel my order", "How do I cancel an order?", "Please help with cancellation", "Can you cancel my purchase?", "I need to cancel now", "Tell me how to cancel"],
        "payment": ["My payment failed", "I was charged twice", "Can you check my payment?", "I need help with payment", "My card payment failed", "Show me the payment policy", "I paid twice for the order"],
        "product_info": ["What is the product price?", "Tell me the product details", "How much does it cost?", "I need product information", "Show me the fee", "What is the cost for bootcamp?", "Can you tell me about laptop hardware?"]
    },
    "hi": {
        "refund": ["मुझे रिफंड चाहिए", "पैसे वापस लेने के नियम बताओ", "रिफंड नीति क्या है", "mujhe paise wapas chahiye", "mera refund kab aayega", "mujhey refnd chahie", "paise vapas kaise milenge"],
        "delivery_status": ["मेरा ऑर्डर कहाँ है", "डिलीवरी कब आएगी", "ऑर्डर की डिलीवरी बताओ", "mera order kab aayega", "meri delivery kahan hai", "mujhe shipping batao", "order kaha hai bataiye"],
        "cancel_order": ["मेरा ऑर्डर रद्द करो", "ऑर्डर रद्द करना है", "कृपया ऑर्डर रद्द करें", "mera order cancel karo", "mujhe order band karo", "order cancel karna hai", "mera order khatam karo"],
        "payment": ["मेरा भुगतान विफल हुआ", "पेमेंट की जानकारी चाहिए", "भुगतान के नियम बताओ", "mera payment failed hua", "mujhe payment batao", "meri card payment failed hai", "payment kaise karna hai"],
        "product_info": ["उत्पाद की कीमत क्या है", "कीमत बताओ", "मुझे कीमत जाननी है", "product price kitna hai", "mera product price batao", "mujhe product details chahiye", "product ka cost kya hai"]
    },
    "te": {
        "refund": ["నాకు డబ్బు తిరిగి కావాలి", "రీఫండ్ నియమాలు చెప్పండి", "నా రీఫండ్ గురించి చెప్పండి", "naaku dabbu tirigi kavali", "naa refund eppudu vastundi", "naku refnd kavali", "refund ela pondali"],
        "delivery_status": ["నా ఆర్డర్ డెలివరీ ఎప్పుడు", "డెలివరీ వివరాలు చెప్పండి", "నా డెలివరీ ఎక్కడ ఉంది", "naa order eppudu vastundi", "delivery ekkada undi", "naaku shipping vivaralu kavali", "order epudu vasthundi cheppandi"],
        "cancel_order": ["నా ఆర్డర్ రద్దు చేయండి", "ఆర్డర్ రద్దు చేయాలి", "దయచేసి ఆర్డర్ రద్దు చేయండి", "naa order raddu cheyandi", "order cancel cheyali", "naaku order cancel cheyandi", "naa order raddhu cheyyandi"],
        "payment": ["నా చెల్లింపు విఫలమైంది", "పేమెంట్ వివరాలు చెప్పండి", "చెల్లింపు గురించి చెప్పండి", "naa payment failed ayyindi", "naaku payment vivaralu kavali", "card payment failed ayindi", "payment ela cheyali"],
        "product_info": ["ఉత్పత్తి ధర ఎంత", "ధర చెప్పండి", "ఉత్పత్తి ధర వివరాలు కావాలి", "product price entha", "naaku product details kavali", "product cost entha cheppu", "naa product price teliyali"]
    },
    "es": {
        "refund": ["Quiero un reembolso", "Necesito un reembolso por favor", "Cuál es la política de devolución", "Puedes ver las reglas de reembolso", "Quiero información de devolución", "Necesito rembolso por favor", "Cómo obtengo un reembolso"],
        "delivery_status": ["Dónde está mi pedido", "Cuándo llega mi pedido", "Necesito información de entrega", "Quiero ver el envío", "Puedes ver la entrega del pedido", "Dónde esta el pedido", "Cuándo llega la entrega"],
        "cancel_order": ["Quiero cancelar mi pedido", "Cancela el pedido por favor", "Necesito cancelar un pedido", "Cómo cancelar el pedido", "Quiero información de cancelación", "Puedes cancelar mi pedido", "Necesito ayuda para cancelar"],
        "payment": ["Mi pago falló", "Necesito ayuda con el pago", "Quiero información del pago", "Me han cobrado dos veces", "Puedes ver mi pago", "El pago fallo otra vez", "Necesito saber la política de pago"],
        "product_info": ["Cuál es el precio del producto", "Necesito información del producto", "Cuánto cuesta el producto", "Quiero ver el precio", "Puedes ver el coste del producto", "El precio del producto por favor", "Necesito saber el precio"]
    }
}

CONTINUATIONS = {
    "en": ("sorry, order {new} not {old}", "any update on it?"),
    "hi": ("माफ़ करें, ऑर्डर {new} नहीं {old}", "वही"),
    "te": ("క్షమించండి, ఆర్డర్ {new} కాదు {old}", "అదే"),
    "es": ("perdón, pedido {new} no {old}", "ese mismo")
}

UNSEEN = {
    "en": [("Please show refund rules for my bootcamp enrollment", "refund"), ("Can you track the shipping for my purchase now", "delivery_status"), ("I want to cancel that order instead", "cancel_order"), ("Help me with the card payment please", "payment"), ("Can you show the cost and product details", "product_info")],
    "hi": [("mujhe bootcamp ke paise vapas chahiye please", "refund"), ("meri shipping kab ayega bataiye please", "delivery_status"), ("order raddu nahi cancel karo", "cancel_order"), ("mere payment ke rules samjhao", "payment"), ("kripya product price bataiye", "product_info")],
    "te": [("dayachesi naaku bootcamp refund vivaralu cheppandi", "refund"), ("naa shipping epudu vasthundi cheppu", "delivery_status"), ("dayachesi order raddhu cheyali", "cancel_order"), ("naaku card payment kosam help kavali", "payment"), ("product price entha untundi cheppandi", "product_info")],
    "es": [("Por favor quiero saber las reglas del reembolso", "refund"), ("Puedes ver dónde está la entrega de mi compra", "delivery_status"), ("Quiero ayuda para cancelar ese pedido", "cancel_order"), ("Por favor necesito información de mi pago", "payment"), ("Puedes mostrar el precio del producto por favor", "product_info")]
}


def write_fixtures() -> None:
    output = ROOT / "tests/fixtures"
    output.mkdir(parents=True, exist_ok=True)
    counts = {}
    for language, by_intent in QUESTIONS.items():
        conversations = []
        for intent, questions in by_intent.items():
            for i, question in enumerate(questions):
                old, new = str(4500 + len(conversations)), str(5500 + len(conversations))
                correction, followup = CONTINUATIONS[language]
                conversations.append({"id": f"{language}-{intent}-{i}", "language": language,
                                      "messages": [{"text": question, "intents": [intent]},
                                                   {"text": correction.format(new=new, old=old), "intents": ["correction"]},
                                                   {"text": followup, "intents": [intent]}],
                                      "latest_order": new, "superseded_order": old})
        (output / f"{language}.json").write_text(json.dumps(conversations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        counts[language] = len(conversations)
    unseen = [{"id": f"unseen-{language}-{i}", "language": language,
               "messages": [{"text": text, "intents": [intent]}]}
              for language, cases in UNSEEN.items() for i, (text, intent) in enumerate(cases)]
    (output / "unseen.json").write_text(json.dumps(unseen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"conversations_per_language": counts, "unseen_conversations": len(unseen)}, sort_keys=True))


if __name__ == "__main__":
    write_fixtures()
