"""Generate synthetic PDF fixtures for salary extraction evals.

Run: python -m tests.evals.generate_fixtures
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

FIXTURES_DIR = Path(__file__).parent / "assets" / "fixtures"


def _make_pdf(text: str, filename: str) -> Path:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in text.split("\n"):
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    path = FIXTURES_DIR / filename
    pdf.output(str(path))
    return path


def generate() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    _make_pdf(
        """ACME Corporation
Pay Statement - Biweekly

Employee: Sarah J. Mitchell
Pay Period: 01/01/2024 - 01/14/2024
Pay Date: 01/19/2024
Pay Frequency: Biweekly

                    Current         YTD
Gross Pay:         $3,653.85       $3,653.85
Federal Tax:         $547.00         $547.00
State Tax:           $182.69         $182.69
Social Security:     $226.54         $226.54
Medicare:             $52.98          $52.98
Net Pay:           $2,644.64       $2,644.64

Annual Salary: $95,000.00
""",
        "paystub-acme-biweekly.pdf",
    )

    _make_pdf(
        """TechForward Inc.
Pay Statement - Monthly

Employee: James R. Chen
Pay Period: 01/01/2024 - 01/31/2024
Pay Date: 02/05/2024
Pay Frequency: Monthly

                    Current         YTD
Gross Pay:        $10,000.00      $10,000.00
Federal Tax:       $1,500.00       $1,500.00
State Tax:           $500.00         $500.00
Social Security:     $620.00         $620.00
Medicare:            $145.00         $145.00
Net Pay:           $7,235.00       $7,235.00

Annual Salary: $120,000.00
""",
        "paystub-techforward-monthly.pdf",
    )

    _make_pdf(
        """Greenleaf Services LLC
Pay Statement - Weekly

Employee: Maria L. Torres
Pay Period: 01/01/2024 - 01/07/2024
Pay Date: 01/12/2024
Pay Frequency: Weekly

Hourly Rate: $40.00
Hours Worked: 40.0
Gross Pay: $1,600.00
YTD Gross: $1,600.00

Federal Tax:    $240.00
State Tax:      $80.00
Net Pay:      $1,280.00
""",
        "paystub-greenleaf-weekly.pdf",
    )

    _make_pdf(
        """W-2 Wage and Tax Statement 2024

Employer: ACME Corporation
EIN: 12-3456789

Employee: Sarah J. Mitchell
SSN: XXX-XX-1234

Box 1 - Wages, tips, other compensation: $95,000.00
Box 2 - Federal income tax withheld: $14,222.00
Box 3 - Social security wages: $95,000.00
Box 4 - Social security tax withheld: $5,890.00
Box 5 - Medicare wages and tips: $95,000.00
Box 6 - Medicare tax withheld: $1,377.50
""",
        "w2-acme-2024.pdf",
    )

    _make_pdf(
        """ACME Corporation
123 Business Ave, Suite 100
New York, NY 10001

January 15, 2024

Dear Sarah J. Mitchell,

We are pleased to offer you the position of Senior Software Engineer
at ACME Corporation.

Position: Senior Software Engineer
Department: Engineering
Start Date: February 1, 2024
Annual Salary: $95,000.00
Pay Frequency: Biweekly

Benefits include health insurance, 401(k) matching, and 15 days PTO.

Please sign and return this letter by January 25, 2024.

Sincerely,
John Smith
VP of Engineering
""",
        "offer-letter-acme.pdf",
    )

    _make_pdf(
        """TechForward Inc.
456 Innovation Blvd
San Francisco, CA 94105

TO WHOM IT MAY CONCERN

This letter confirms that James R. Chen is currently employed at
TechForward Inc. as a Data Scientist.

Start Date: March 15, 2023
Current Annual Salary: $120,000.00
Employment Status: Full-time

This letter is provided at the request of the employee for
verification purposes only.

Sincerely,
HR Department
TechForward Inc.
""",
        "employment-verification-techforward.pdf",
    )

    print(f"Generated fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    generate()
