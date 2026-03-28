#!/usr/bin/env python3
"""Generate synthetic legal sample documents for DraftForge.

Creates 5 mock documents in sample_documents/:
  - lease_agreement.pdf     (multi-page PDF with extractable text)
  - handwritten_note.png    (noisy image simulating handwriting / OCR challenge)
  - case_filing.txt         (text with OCR-style artifacts)
  - property_deed.pdf       (PDF styled to look like a degraded scan)
  - notice_letter.txt       (clean text baseline)

Run from the backend/ directory:
    python scripts/generate_samples.py
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

SAMPLES_DIR = Path("sample_documents")


def create_lease_agreement():
    """Multi-page PDF with extractable text — structured legal language."""
    path = SAMPLES_DIR / "lease_agreement.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            topMargin=1 * inch, bottomMargin=1 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=20)
    heading = ParagraphStyle("H2", parent=styles["Heading2"], spaceAfter=10, spaceBefore=16)
    body = ParagraphStyle("Body2", parent=styles["BodyText"], fontSize=11,
                          leading=15, spaceAfter=8)

    story = []

    story.append(Paragraph("RESIDENTIAL LEASE AGREEMENT", title_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("SECTION 1 — PARTIES AND PROPERTY", heading))
    story.append(Paragraph(
        "This Residential Lease Agreement (\"Agreement\") is entered into as of "
        "January 15, 2024, by and between GREENFIELD PROPERTIES LLC, a Delaware "
        "limited liability company (\"Landlord\"), and JAMES WHITMORE AND SARAH "
        "WHITMORE, individuals (\"Tenant\"), collectively referred to as the \"Parties\".",
        body,
    ))
    story.append(Paragraph(
        "The Landlord hereby leases to the Tenant the residential property located at "
        "1847 Oak Valley Drive, Unit 4B, Springfield, IL 62704 (\"Premises\"), "
        "including all fixtures, appliances, and furnishings currently present.",
        body,
    ))

    story.append(Paragraph("SECTION 2 — TERM AND RENT", heading))
    story.append(Paragraph(
        "The lease term shall commence on February 1, 2024, and shall terminate on "
        "January 31, 2025, unless renewed or terminated earlier pursuant to the terms "
        "herein. The monthly rent shall be $2,450.00, due on the first day of each "
        "calendar month. A security deposit of $4,900.00 shall be collected upon "
        "execution of this Agreement.",
        body,
    ))
    story.append(Paragraph(
        "Late payment penalty: If rent is not received by the 5th day of the month, "
        "a late fee of $125.00 shall be assessed. Returned check fee: $50.00. "
        "All payments shall be made by check or electronic transfer to the account "
        "designated by the Landlord.",
        body,
    ))

    story.append(Paragraph("SECTION 3 — MAINTENANCE AND REPAIRS", heading))
    story.append(Paragraph(
        "The Landlord shall maintain the structural components of the Premises, "
        "including the roof, exterior walls, foundation, plumbing, electrical, and "
        "HVAC systems. The Tenant shall be responsible for routine maintenance, "
        "including lawn care, pest control, and minor repairs not exceeding $200.00.",
        body,
    ))
    story.append(Paragraph(
        "The Tenant shall promptly notify the Landlord of any condition requiring "
        "repair. The Landlord shall respond within 48 hours for urgent matters "
        "(water leaks, heating failure, security issues) and within 14 days for "
        "non-urgent repairs.",
        body,
    ))

    story.append(Paragraph("SECTION 4 — TERMINATION AND DEFAULT", heading))
    story.append(Paragraph(
        "Either party may terminate this Agreement with sixty (60) days written "
        "notice prior to the end of the lease term. In the event of a material "
        "breach by the Tenant, including non-payment of rent for more than thirty "
        "(30) days or violation of the property use restrictions in Section 5, "
        "the Landlord may initiate eviction proceedings in accordance with "
        "Illinois Compiled Statutes 735 ILCS 5/9-101 et seq.",
        body,
    ))

    story.append(Paragraph("SECTION 5 — PROPERTY USE RESTRICTIONS", heading))
    story.append(Paragraph(
        "The Premises shall be used exclusively for residential purposes. The "
        "Tenant shall not sublet or assign this lease without the prior written "
        "consent of the Landlord. No pets are permitted without a separate pet "
        "addendum. The Tenant shall not engage in any activity that constitutes "
        "a nuisance or violates any applicable local, state, or federal law.",
        body,
    ))

    story.append(Paragraph("SECTION 6 — GOVERNING LAW", heading))
    story.append(Paragraph(
        "This Agreement shall be governed by and construed in accordance with the "
        "laws of the State of Illinois. Any disputes arising hereunder shall be "
        "resolved in the Circuit Court of Sangamon County, Illinois. "
        "Case File No. LL-2024-00417.",
        body,
    ))

    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "IN WITNESS WHEREOF, the Parties have executed this Agreement as of the "
        "date first written above.",
        body,
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("________________________________<br/>Landlord: Greenfield Properties LLC", body))
    story.append(Spacer(1, 12))
    story.append(Paragraph("________________________________<br/>Tenant: James Whitmore", body))
    story.append(Spacer(1, 12))
    story.append(Paragraph("________________________________<br/>Tenant: Sarah Whitmore", body))

    doc.build(story)
    print(f"  Created {path}")


def create_handwritten_note():
    """Noisy PNG image simulating a scanned handwritten note."""
    import random
    width, height = 800, 600
    img = Image.new("RGB", (width, height), "#f5f0e1")
    draw = ImageDraw.Draw(img)

    # Try to use a built-in font; fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small_font = font

    lines = [
        "CLIENT MEETING NOTES - March 12, 2024",
        "",
        "Re: HARRISON v. OAKMONT DEVELOPMENT CORP",
        "Case No. CV-2024-03892",
        "",
        "Key Points Discussed:",
        "- Property dispute at 445 Birch Lane, contested boundary",
        "- Survey from 2019 shows encroachment of approx 12 feet",
        "- Defendant claims adverse possession (need to verify",
        "  statute of limitations - check 735 ILCS 5/13-101)",
        "- Settlement demand: $85,000 + survey costs ($3,200)",
        "- Client prefers mediation before litigation",
        "",
        "Action Items:",
        "1) Pull county records for parcel #12-34-567-008",
        "2) Contact surveyor Jim Hendricks - (217) 555-0142",
        "3) Draft demand letter by March 20, 2024",
        "4) Schedule mediation - Judge Calloway's office",
        "",
        "Next meeting: March 25, 2024 at 2:00 PM",
    ]

    y = 30
    for line in lines:
        x_offset = random.randint(-2, 2)
        color_var = random.randint(20, 60)
        color = (color_var, color_var, color_var + 10)
        f = small_font if line.startswith((" ", "-", "1", "2", "3", "4")) else font
        draw.text((40 + x_offset, y), line, fill=color, font=f)
        y += 26

    # Add noise / aging effect
    random.seed(42)
    for _ in range(800):
        x = random.randint(0, width - 1)
        y_noise = random.randint(0, height - 1)
        shade = random.randint(160, 210)
        draw.point((x, y_noise), fill=(shade, shade - 10, shade - 20))

    # Coffee stain (semi-transparent circle)
    for _ in range(3):
        cx, cy = random.randint(500, 700), random.randint(100, 400)
        r = random.randint(30, 60)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 180, 140), width=2)

    path = SAMPLES_DIR / "handwritten_note.png"
    img.save(str(path), "PNG")
    print(f"  Created {path}")


def create_case_filing():
    """Text file with simulated OCR artifacts — garbled characters, broken line breaks."""
    content = """UNITED STATES DISTRICT COURT
CENTRAL DISTRICT OF ILLlNOIS

MARTHA REYNOLDS,          )
       Plaintiff,         )   Case No. 3:2024-CV-00156
                           )
   vs.                     )   Judge Patricia Hawkins
                           )
SUMMIT HEALTHCARE GR0UP,  )   Filed: February 28, 2024
       Defendant.          )

COMPLAINT FOR MEDICAL MALPRACT1CE

I. PARTIES

1. P1aintiff MARTHA REYNOLDS ("Plaintiff") is a resident of Springfield,
Sangamon County, l1linois.

2. Defendant SUMMIT HEALTHCARE GROUP ("Defendant") is a c0rporation
organized under the 1aws of the State of Illinois, with its principal p1ace
of business at 2200 Medical Center Drive, Springfield, IL 62702.

II. JURISDICTI0N AND VENUE

3. This Court has jurisdiction pursuant to 28 U.S.C. § 1332, as the
amount in contr0versy exceeds $75,000.00 and the parties are diverse.

4. Venue is proper in this District pursuant to 28 U.S.C. § l391(b).

III. STATEMENT 0F FACTS

5. On or about September 15, 2023, Plaintiff presented to Defendant's
faci1ity at Springfield Memorial Hospita1 for treatment of persistent
abdominal pain.

6. Dr. Robert Chen, an emp1oyee and/or agent of Defendant, performed a
diagnostic evaluation and recommended an appendect0my procedure.

7. During the surgical procedure on September 17, 2023, Dr. Chen
negligent1y perforated the Plaintiff's b0wel, causing severe internal
infection and comp1ications.

8. As a direct resu1t of Defendant's negligence, Plaintiff suffered:
   a) Extended hospitalization of 23 days (September 17 - 0ctober 10, 2023)
   b) Two additional corrective surgeries
   c) Permanent scarring and reduced digestive function
   d) Medical expenses t0taling $347,892.00
   e) Lost wages of $42,500.00
   f) Ongoing pain, suffering, and emoti0nal distress

IV. CAUSES 0F ACTION

Count I - Medical Ma1practice

9. Defendant, through its agents and emp1oyees, owed a duty of care to
Plaintiff consistent with the accepted standard of medica1 practice.

10. Defendant breached this duty by failing to exercise reas0nable care
during the surgical procedure.

11. As a proximate resu1t of Defendant's breach, Plaintiff has suffered
and continues to suffer damages in excess of $500,000.00.

V. PRAYER F0R RELIEF

WHEREFORE, Plaintiff respectfully requests that this Court:

   a) Award compensatory damages in an am0unt to be determined at trial,
      but not less than $500,000.00;
   b) Award punitive damages for Defendant's reckless c0nduct;
   c) Award costs of suit and reas0nable attorney's fees; and
   d) Grant such other re1ief as this Court deems just and proper.

Respectful1y submitted,

/s/ David Morales
David M0rales, Esq.
Illinois Bar N0. 6284913
Morales & Associates, LLC
1500 Capitol Avenue, Suite 300
Springfield, IL 62701
(217) 555-0198
dmorales@moraleslaw.c0m

Dated: February 28, 2024
"""
    path = SAMPLES_DIR / "case_filing.txt"
    path.write_text(content)
    print(f"  Created {path}")


def create_property_deed():
    """PDF that looks like a degraded / scanned property deed."""
    path = SAMPLES_DIR / "property_deed.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DeedTitle", parent=styles["Title"],
                                 fontSize=16, spaceAfter=16)
    body = ParagraphStyle("DeedBody", parent=styles["BodyText"],
                          fontSize=10, leading=14, spaceAfter=6)
    heading = ParagraphStyle("DeedH", parent=styles["Heading3"],
                             spaceAfter=8, spaceBefore=12)

    story = []

    story.append(Paragraph("WARRANTY DEED", title_style))
    story.append(Paragraph("Sangamon County, Illinois", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Document No. DEED-2024-00823<br/>"
        "Recording Date: January 8, 2024<br/>"
        "Parcel Identification Number: 14-28-376-009",
        body,
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("GRANTOR AND GRANTEE", heading))
    story.append(Paragraph(
        "KNOW ALL MEN BY THESE PRESENTS, that ROBERT L. FISCHER AND LINDA M. "
        "FISCHER, husband and wife (\"Grantor\"), of Springfield, Sangamon County, "
        "Illinois, for and in consideration of the sum of THREE HUNDRED FORTY-FIVE "
        "THOUSAND DOLLARS ($345,000.00) and other good and valuable consideration, "
        "receipt of which is hereby acknowledged, does hereby GRANT, BARGAIN, SELL "
        "AND CONVEY unto DAVID PARK AND ELENA PARK, husband and wife, as joint "
        "tenants with right of survivorship (\"Grantee\"), the following described "
        "real property:",
        body,
    ))

    story.append(Paragraph("LEGAL DESCRIPTION", heading))
    story.append(Paragraph(
        "Lot 23 in Block 7 of WESTFIELD ESTATES SUBDIVISION, being a subdivision "
        "of part of the Southeast Quarter of Section 28, Township 16 North, Range 5 "
        "West of the Third Principal Meridian, according to the Plat thereof recorded "
        "in Plat Book 42, Page 118, in the Office of the Recorder of Deeds, Sangamon "
        "County, Illinois.",
        body,
    ))
    story.append(Paragraph(
        "Common Address: 892 Westfield Circle, Springfield, IL 62711",
        body,
    ))

    story.append(Paragraph("ENCUMBRANCES AND EXCEPTIONS", heading))
    story.append(Paragraph(
        "Subject to: (a) Real estate taxes for the year 2024 and subsequent years, "
        "not yet due and payable; (b) Easement in favor of Ameren Illinois for "
        "electrical utility along the north 10 feet of said lot, as recorded in "
        "Document No. 2019-R-04521; (c) Restrictive covenants of Westfield Estates "
        "Homeowners Association, recorded in Document No. 2005-R-12847; (d) Building "
        "setback lines as shown on the recorded plat.",
        body,
    ))

    story.append(Paragraph("WARRANTY", heading))
    story.append(Paragraph(
        "Grantor hereby warrants that Grantor is lawfully seized of said property "
        "in fee simple, that the property is free from all encumbrances except as "
        "stated above, and that Grantor will defend the title to said property against "
        "the lawful claims of all persons whomsoever.",
        body,
    ))

    story.append(Paragraph("TAX INFORMATION", heading))
    story.append(Paragraph(
        "Prior Year (2023) Real Estate Taxes: $6,847.32<br/>"
        "Tax Rate: 1.984% of assessed value<br/>"
        "Assessed Value: $345,100.00<br/>"
        "Tax Parcel PIN: 14-28-376-009<br/>"
        "Homestead Exemption Applied: Yes",
        body,
    ))

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        "IN WITNESS WHEREOF, the Grantor has executed this instrument on the "
        "8th day of January, 2024.",
        body,
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("________________________________<br/>Robert L. Fischer", body))
    story.append(Spacer(1, 12))
    story.append(Paragraph("________________________________<br/>Linda M. Fischer", body))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        "STATE OF ILLINOIS )<br/>"
        "                  ) SS.<br/>"
        "COUNTY OF SANGAMON )",
        body,
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "I, the undersigned Notary Public, do hereby certify that ROBERT L. FISCHER "
        "AND LINDA M. FISCHER, personally known to me to be the same persons whose "
        "names are subscribed to the foregoing instrument, appeared before me this "
        "day in person and acknowledged that they signed, sealed, and delivered the "
        "said instrument as their free and voluntary act.",
        body,
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Notary Public: Maria Gonzalez<br/>"
        "Commission Expires: June 30, 2026<br/>"
        "Notary Seal No. 7841923",
        body,
    ))

    doc.build(story)
    print(f"  Created {path}")


def create_notice_letter():
    """Clean text file — a formal notice letter (baseline test)."""
    content = """MORALES & ASSOCIATES, LLC
Attorneys at Law
1500 Capitol Avenue, Suite 300
Springfield, IL 62701
Phone: (217) 555-0198

March 5, 2024

Via Certified Mail - Return Receipt Requested

Summit Healthcare Group
Attn: Legal Department
2200 Medical Center Drive
Springfield, IL 62702

Re: Notice of Intent to File Medical Malpractice Action
    Martha Reynolds v. Summit Healthcare Group
    Date of Incident: September 17, 2023

Dear Sir or Madam:

Please be advised that this firm represents Martha Reynolds in connection with
injuries sustained during a surgical procedure performed at Springfield Memorial
Hospital on September 17, 2023.

Pursuant to 735 ILCS 5/2-622, this letter serves as formal notice of our
client's intent to file a medical malpractice action against Summit Healthcare
Group and its agents, including but not limited to Dr. Robert Chen.

SUMMARY OF CLAIM:

On September 15, 2023, our client presented to your facility with complaints of
persistent abdominal pain. After diagnostic evaluation, Dr. Robert Chen
recommended an appendectomy procedure, which was performed on September 17, 2023.

During the surgical procedure, Dr. Chen negligently perforated our client's
bowel, resulting in severe peritonitis and requiring two additional corrective
surgeries. Our client was hospitalized for 23 days (September 17 through
October 10, 2023) and continues to suffer from permanent complications.

DAMAGES:

Our client has incurred the following damages to date:

    Medical expenses:                    $347,892.00
    Lost wages (September - December):    $42,500.00
    Estimated future medical costs:      $125,000.00
    Pain and suffering:                  To be determined

    Total economic damages to date:      $515,392.00

DEMAND:

We hereby demand that Summit Healthcare Group and its insurers:

1. Preserve all medical records, incident reports, quality assurance documents,
   and communications related to our client's care;
2. Forward this notice to your medical malpractice insurance carrier;
3. Provide the name and contact information of your designated claims
   representative within fourteen (14) days of receipt of this letter.

We are prepared to discuss settlement of this matter prior to the filing of
formal litigation. However, if we do not receive a substantive response within
thirty (30) days of receipt of this notice, we will proceed with filing a
complaint in the Circuit Court of Sangamon County, Illinois.

Please direct all communications regarding this matter to the undersigned.

Respectfully,

David Morales, Esq.
Illinois Bar No. 6284913
Morales & Associates, LLC
dmorales@moraleslaw.com

cc: Martha Reynolds (client)
    Illinois Department of Financial and Professional Regulation
"""
    path = SAMPLES_DIR / "notice_letter.txt"
    path.write_text(content)
    print(f"  Created {path}")


def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating sample legal documents...")
    create_lease_agreement()
    create_handwritten_note()
    create_case_filing()
    create_property_deed()
    create_notice_letter()
    print(f"\nDone! {len(list(SAMPLES_DIR.iterdir()))} documents created in {SAMPLES_DIR}/")


if __name__ == "__main__":
    main()
