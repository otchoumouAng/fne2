import os
import asyncio
import qrcode
import base64
import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from num2words import num2words


class PDFGenerator:
    def __init__(self, template_file):
        if not template_file:
            raise ValueError("Un nom de fichier de template est requis.")

        # Définir les chemins de base
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = script_dir.parent
        template_dir_path = self.project_root / 'templates'
        self.images_dir = self.project_root / 'images'

        # Configurer Jinja
        self.env = Environment(loader=FileSystemLoader(template_dir_path))
        self.env.globals['money'] = self.money
        self.template = self.env.get_template(template_file)

    def _image_to_base64_uri(self, img):
        """Convertit une image PIL en data URI Base64."""
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    def _file_to_base64_uri(self, filepath):
        """Convertit un fichier image en data URI Base64."""
        try:
            with open(filepath, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded_string}"
        except FileNotFoundError:
            return None

    def generate_qr_code(self, data):
        """Génère un QR code et le retourne en tant que data URI Base64."""
        if not data:
            return None

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        return self._image_to_base64_uri(img)

    # @staticmethod
    # def money(value, currency="XOF"):
    #     if value is None:
    #         value = 0
    #     try:
    #         return f"{float(value):,.2f} {currency}".replace(",", " ")
    #     except (ValueError, TypeError):
    #         return f"{0:,.2f} {currency}".replace(",", " ")

    @staticmethod
    def money(value, currency="XOF"):
        if value is None:
            value = 0
        try:
            return f"{float(value):,g} {currency}".replace(",", " ")
        except (ValueError, TypeError):
            # Utiliser aussi :,g ici
            return f"{0:,g} {currency}".replace(",", " ")


    @staticmethod
    def currency_to_words(currency):
        mapping = {"XOF": "francs CFA", "EUR": "euros", "USD": "dollars"}
        return mapping.get(currency, currency)

    def money_to_words(self, value, currency="XOF"):
        try:
            words = num2words(value, lang="fr")
            return f"{words} {self.currency_to_words(currency)}"
        except NotImplementedError:
            return str(value)

    # def render_html(self, **context):
    #     details = context.get('details', [])
        
    #     context['entreprise_logo_uri'] = self._file_to_base64_uri(self.images_dir / 'entreprise_logo.png')

    #     # Initialiser les totaux pour qu'ils existent toujours dans le contexte
    #     subtotal, taxes, grand_total, total_tax = 0, {}, 0, 0

    #     if details:
    #         for item in details:
    #             line_ht = item.get("quantity", 0) * item.get("unit_price", 0)
    #             subtotal += line_ht
    #             tax_rate = item.get("tax_rate", 0)
    #             tax_amt = line_ht * tax_rate / 100
    #             taxes[tax_rate] = taxes.get(tax_rate, 0) + tax_amt
    #         total_tax = sum(taxes.values())
    #         grand_total = subtotal + total_tax

    #     context.update({
    #         'subtotal': subtotal,
    #         'taxes': taxes,
    #         'total_tax': total_tax,
    #         'grand_total': grand_total,
    #         'grand_total_words': self.money_to_words(grand_total),
    #         'qr_code_uri': None,
    #         'fne_logo_uri': None
    #     })


    #     # Ajouter le logo de l'entreprise
    #     logo_path = self.images_dir / 'logo_sogici.png'
    #     context['logo_uri'] = self._file_to_base64_uri(logo_path)

    #     # Générer le QR code si les données FNE sont présentes
    #     fne_qr_code_data = None
    #     if self.template.name == 'invoice.html':
    #         invoice_details = context.get('invoice', {})
    #         fne_qr_code_data = invoice_details.get('fne_qr_code')
    #     elif self.template.name == 'avoir.html':
    #         avoir_details = context.get('invoice', {})
    #         fne_qr_code_data = avoir_details.get('fne_qr_code')

    #     if fne_qr_code_data:
    #         context['qr_code_uri'] = self.generate_qr_code(fne_qr_code_data)

    #         # Ajouter le logo FNE
    #         fne_logo_path = self.images_dir / 'fne.png'
    #         context['fne_logo_uri'] = self._file_to_base64_uri(fne_logo_path)


    #     return self.template.render(**context)

    

    def render_html(self, **context):
        details = context.get('details', [])
        
        context['entreprise_logo_uri'] = self._file_to_base64_uri(self.images_dir / 'entreprise_logo.png')

        # Initialiser les totaux pour qu'ils existent toujours dans le contexte
        subtotal, taxes, grand_total, total_tax = 0, {}, 0, 0

        if details:
            for item in details:
                line_ht = item.get("quantity", 0) * item.get("unit_price", 0)
                subtotal += line_ht
                tax_rate = item.get("tax_rate", 0)
                tax_amt = line_ht * tax_rate / 100
                taxes[tax_rate] = taxes.get(tax_rate, 0) + tax_amt
        
        # --- DEBUT DE LA CORRECTION D'ARRONDI ---
        
        # Arrondir le sous-total (par sécurité)
        subtotal = round(subtotal, 2)

        # Arrondir les montants de taxes calculés
        rounded_taxes = {}
        for rate, amt in taxes.items():
            rounded_taxes[rate] = round(amt, 2)
        
        # Calculer les totaux finaux à partir des valeurs arrondies
        total_tax = round(sum(rounded_taxes.values()), 2)
        grand_total = round(subtotal + total_tax, 2)
        
        # --- FIN DE LA CORRECTION D'ARRONDI ---

        context.update({
            'subtotal': subtotal,
            'taxes': rounded_taxes,       # Utiliser les taxes arrondies
            'total_tax': total_tax,       # Utiliser le total de taxe arrondi
            'grand_total': grand_total,   # Utiliser le total général arrondi
            'grand_total_words': self.money_to_words(grand_total), # Basé sur le MÊME total arrondi
            'qr_code_uri': None,
            'fne_logo_uri': None
        })


        # Ajouter le logo de l'entreprise
        logo_path = self.images_dir / 'entreprise_logo.png'
        context['logo_uri'] = self._file_to_base64_uri(logo_path)

        # Générer le QR code si les données FNE sont présentes
        fne_qr_code_data = None
        if self.template.name == 'invoice.html':
            invoice_details = context.get('invoice', {})
            fne_qr_code_data = invoice_details.get('fne_qr_code')
        elif self.template.name == 'avoir.html':
            avoir_details = context.get('invoice', {})
            fne_qr_code_data = avoir_details.get('fne_qr_code')

        if fne_qr_code_data:
            context['qr_code_uri'] = self.generate_qr_code(fne_qr_code_data)

            # Ajouter le logo FNE
            fne_logo_path = self.images_dir / 'fne.png'
            context['fne_logo_uri'] = self._file_to_base64_uri(fne_logo_path)


        return self.template.render(**context)

    async def generate_pdf(self, html_content, output_file="document.pdf"):
        # Lire le contenu du fichier CSS
        # css_path = self.project_root / 'templates' / 'style.css'
        # try:
        #     with open(css_path, 'r') as f:
        #         css_content = f.read()
        # except FileNotFoundError:
        #     css_content = "" # Continuer sans CSS si le fichier n'est pas trouvé

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)

            # Injecter le CSS
            # if css_content:
            #     await page.add_style_tag(content=css_content)

            await page.pdf(
                path=output_file,
                format="A4",
                print_background=True,
                display_header_footer=True,
                footer_template="""
                <div style="font-size:10px; width:100%; text-align:center; color:#555; padding-top:5px;">
                    Merci pour votre confiance — Page <span class="pageNumber"></span> / <span class="totalPages"></span>
                </div>
                """,
                header_template="<div></div>",
                margin={"top": "5mm", "bottom": "10mm"}
            )
            await browser.close()
        print(f"✅ Document PDF généré : {output_file}")