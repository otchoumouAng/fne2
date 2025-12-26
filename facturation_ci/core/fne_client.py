import requests
import json

# L'URL de base de l'API FNE. À mettre dans un fichier de configuration dans une app réelle.
FNE_API_BASE_URL = "http://54.247.95.108/ws/external"

class FNEClientError(Exception):
    """Exception personnalisée pour les erreurs du client FNE."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

def certify_document(invoice_full_data: dict, company_info: dict, client_info: dict, user_info: dict, api_key: str):
    """
    Appelle l'API FNE pour certifier un document de vente ou d'achat.

    :param invoice_full_data: Dictionnaire contenant les détails de la facture et les lignes d'articles ('details' et 'items').
    :param company_info: Dictionnaire avec les informations de l'entreprise.
    :param client_info: Dictionnaire avec les informations du client.
    :param user_info: Dictionnaire avec les informations de l'opérateur.
    :param api_key: La clé d'API de l'entreprise pour l'authentification.
    :return: Dictionnaire avec les données de certification FNE.
    :raises FNEClientError: En cas d'échec de la communication ou d'erreur de l'API.
    """
    invoice_details = invoice_full_data['details']
    doc_type = invoice_details['document_type']  # 'sale', 'purchase'

    if doc_type not in ["sale", "purchase"]:
        raise FNEClientError(f"Le type de document '{doc_type}' n'est pas supporté pour la signature.")

    endpoint = f"{FNE_API_BASE_URL}/invoices/sign"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Construire le payload JSON en fonction du type de document.
    if doc_type == "purchase":
        # Payload pour un BL (achat de notre point de vue)
        # Les informations "client" sont celles de notre propre entreprise.
        payload = {
            "invoiceType": "purchase",
            "paymentMethod": "mobile-money",
            "template": "B2B",
            "clientNcc": company_info.get("ncc"),
            "clientCompanyName": company_info.get("name"),
            "pointOfSale": company_info.get("point_of_sale"),
            "establishment": company_info.get("establishment"),
            "clientPhone": company_info.get("phone"),
            "clientEmail": company_info.get("email"),
            "items": [
                {
                    "reference": str(item.get('id')),
                    "description": item['description'],
                    "quantity": int(item['quantity']),
                    "amount": float(item['unit_price'])
                }
                for item in invoice_full_data.get('items', [])
            ]
        }
    else:  # 'sale'
        # Payload pour une facture de vente
        # Les informations "client" sont celles du client.
        payload = {
            "invoiceType": "sale",
            "paymentMethod": "cash",
            "template": "B2B",
            "clientNcc": '',             
            "clientCompanyName": client_info.get("name"),   # Nom du client
            "pointOfSale": company_info.get("point_of_sale"), # Point de vente de l'entreprise
            "establishment": company_info.get("establishment"),
            "clientPhone": client_info.get("phone"),          # Téléphone du client
            "clientEmail": client_info.get("email"),          # Email du client
            "items": [
                {
                    "reference": str(item.get('id')),
                    "description": item['description'],
                    "quantity": int(item['quantity']),
                    "amount": float(item['unit_price']),
                    "taxes": ["TVA"]
                }
                for item in invoice_full_data.get('items', [])
            ]
        }

    try:
        print("--- Payload FNE ---")
        print(json.dumps(payload, indent=2))
        print("---------------------")
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=20)
        response.raise_for_status()

        response_data = response.json()

        print("--- RESPONSE FNE ---")
        print(response_data)
        print("---------------------")

        if "reference" in response_data and "token" in response_data:
            nim = response_data.get("reference")
            qr_code = response_data.get("token")

            fne_invoice_data = response_data.get("invoice", {})
            fne_invoice_id = fne_invoice_data.get("id")
            fne_created_at = fne_invoice_data.get("createdAt")
            fne_items = fne_invoice_data.get("items", [])

            local_item_ids = [item['id'] for item in invoice_full_data.get('items', [])]
            items_id_map = []
            if len(fne_items) == len(local_item_ids):
                items_id_map = [
                    (fne_item['id'], local_item_id)
                    for fne_item, local_item_id in zip(fne_items, local_item_ids)
                ]

            return {
                "nim": nim,
                "qr_code": qr_code,
                "fne_invoice_id": fne_invoice_id,
                "fne_created_at": fne_created_at,
                "items_id_map": items_id_map
            }

        error_msg = response_data.get('message', json.dumps(response_data))
        raise FNEClientError(f"Réponse inattendue de l'API FNE: {error_msg}", response.status_code)

    except requests.exceptions.HTTPError as e:
        print("--- FNE API HTTP Error Response ---")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
        print("-----------------------------------")
        try:
            error_details = e.response.json().get('message', e.response.text)
        except json.JSONDecodeError:
            error_details = e.response.text
        raise FNEClientError(f"Erreur API FNE ({e.response.status_code}): {error_details}", e.response.status_code)

    except requests.exceptions.RequestException as e:
        raise FNEClientError(f"Erreur de communication avec l'API FNE: {e}")
    except Exception as e:
        raise FNEClientError(f"Erreur inattendue lors de la certification: {e}")


def refund_invoice(api_key: str, original_fne_invoice_id: str, items_to_refund: list):
    """
    Appelle l'API FNE pour créer un avoir (refund) sur une facture existante.

    :param api_key: La clé d'API de l'entreprise.
    :param original_fne_invoice_id: L'ID FNE unique de la facture de vente d'origine.
    :param items_to_refund: Une liste de dictionnaires, chacun avec 'id' (FNE item id) et 'quantity'.
    :return: Dictionnaire avec les données de l'avoir certifié.
    :raises FNEClientError: En cas d'échec.
    """
    # (Le reste de cette fonction 'refund_invoice' est inchangé car
    # elle ne dépend pas de company_info ou client_info)
    
    endpoint = f"{FNE_API_BASE_URL}/invoices/{original_fne_invoice_id}/refund"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Le payload contient uniquement la liste des articles à rembourser
    payload = {"items": items_to_refund}

    try:
        print("--- Payload Avoir FNE ---")
        print(json.dumps(payload, indent=2))
        print("--------------------------")
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=20)
        response.raise_for_status()

        response_data = response.json()


        print("--- FNE API Response (Avoir) ---")
        print(f"Response Body: {response_data}")
        print("------------------------------------------")

        # Une réponse de succès contient les clés 'reference' et 'token' au premier niveau
        if "reference" in response_data and "token" in response_data:
            fne_invoice_data = response_data.get("invoice", {})
            fne_created_at = response_data.get("invoice", {}).get("createdAt")
            return {
                "nim": response_data.get("reference"),
                "qr_code": response_data.get("token"),
                "fne_created_at": fne_created_at
            }

        # Gestion d'une réponse de succès qui n'a pas la structure attendue
        error_msg = response_data.get('message', json.dumps(response_data))
        raise FNEClientError(f"Réponse de succès inattendue de l'API FNE pour l'avoir: {error_msg}", response.status_code)

    except requests.exceptions.HTTPError as e:
        print("--- FNE API HTTP Error Response (Avoir) ---")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
        print("------------------------------------------")
        try:
            error_details = e.response.json().get('message', e.response.text)
        except json.JSONDecodeError:
            error_details = e.response.text
        raise FNEClientError(f"Erreur API FNE ({e.response.status_code}) lors de la création de l'avoir: {error_details}", e.response.status_code)

    except requests.exceptions.RequestException as e:
        raise FNEClientError(f"Erreur de communication avec l'API FNE: {e}")
    except Exception as e:
        raise FNEClientError(f"Erreur inattendue lors de la création de l'avoir: {e}")