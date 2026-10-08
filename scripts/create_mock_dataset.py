"""
Generates a realistic 4-page Campus Regulations PDF handbook for GBPIET.
Covers:
- Academic Regulations & Attendance Rules
- Fee Structure Table
- Hostel Gate Timings & Code of Conduct
- Examination Grading Scale & Contacts
"""

import sys
from pathlib import Path

def create_pdf(output_path: Path):
    pages_content = [
        # Page 1: Academic Regulations & Attendance
        [
            "GBPIET CAMPUS REGULATIONS & ACADEMIC HANDBOOK 2025-2026",
            "GOVIND BALLABH PANT INSTITUTE OF ENGINEERING & TECHNOLOGY",
            "PAURI GARHWAL, UTTARAKHAND - 246194",
            "",
            "SECTION 1: ACADEMIC REGULATIONS & ATTENDANCE POLICY",
            "1.1 Minimum Attendance Requirement:",
            "Students are required to maintain a minimum of 75% attendance in all scheduled lectures,",
            "tutorials, and practical classes in each registered course.",
            "",
            "1.2 Medical and Co-curricular Condonation:",
            "In exceptional circumstances such as medical emergencies or authorized participation in",
            "inter-college IEEE events, a condonation of up to 10% may be granted by the Dean of",
            "Academic Affairs upon submission of verified medical documents within 7 working days.",
            "Students with attendance below 65% are strictly debarred from appearing in end-term exams.",
            "",
            "1.3 Academic Integrity & Plagiarism:",
            "Submitting plagiarized assignments, lab records, or examination malpractice results in an",
            "immediate 'F' grade and disciplinary probation for the remaining semester."
        ],
        # Page 2: Fee Structure Table & Scholarship Policies
        [
            "SECTION 2: SEMESTER FEE STRUCTURE & SCHOLARSHIP POLICIES",
            "",
            "2.1 Academic Fee Breakdown (Per Semester):",
            "Tuition Fee (B.Tech Regular): INR 35,000",
            "Examination & Development Fee: INR 6,500",
            "Hostel Accommodation Fee: INR 12,000",
            "Mess Advance (Per Semester): INR 18,500",
            "Total Standard Semester Fee: INR 72,000",
            "",
            "2.2 Fee Payment Deadlines & Late Fine:",
            "All semester dues must be deposited through the college ERP portal by 15th August for odd",
            "semesters and 15th January for even semesters. A late fine of INR 100 per day applies for the",
            "first 10 days, after which registration is withheld.",
            "",
            "2.3 Merit & Category Scholarships:",
            "Top 5% rank holders in each branch receive a 50% tuition fee waiver.",
            "State scholarship applications (SC/ST/OBC/EWS) must be submitted to the Student Welfare",
            "Office before 30th September annually."
        ],
        # Page 3: Hostel Rules & Gate Timings
        [
            "SECTION 3: HOSTEL REGULATIONS & CAMPUS RESIDENCE",
            "",
            "3.1 Hostel Gate Timings & Curfew:",
            "All residential student hostels operate on strict timings for security reasons.",
            "Main Campus Gate closes at 9:30 PM for all students.",
            "Hostel in-time for Girls Hostel (Gargi Bhawan) is 7:30 PM.",
            "Hostel in-time for Boys Hostel (Raman Bhawan, Aryabhatta Bhawan) is 8:30 PM.",
            "Late entry requires prior written approval from the Chief Warden.",
            "",
            "3.2 Night Out & Leave Permissions:",
            "Students intending to leave the campus overnight must obtain an approved Gate Pass via the",
            "GBPIET Student Mobile App verified by their parent or local guardian.",
            "",
            "3.3 Prohibited Items & Disciplinary Action:",
            "Possession of motorized two-wheelers by first-year hostellers is strictly prohibited.",
            "Electric heaters, immersion rods, and cooking appliances are not permitted in hostel rooms."
        ],
        # Page 4: Examination Grading System & Faculty Directory
        [
            "SECTION 4: EXAMINATION GRADING & CONTACT DIRECTORY",
            "",
            "4.1 10-Point Grading System:",
            "Grade A+ (Outstanding): 10 Grade Points (Marks >= 90%)",
            "Grade A (Excellent): 9 Grade Points (Marks 80% to 89%)",
            "Grade B+ (Very Good): 8 Grade Points (Marks 70% to 79%)",
            "Grade B (Good): 7 Grade Points (Marks 60% to 69%)",
            "Grade C (Fair): 6 Grade Points (Marks 50% to 59%)",
            "Grade P (Pass): 5 Grade Points (Marks 40% to 49%)",
            "Grade F (Fail): 0 Grade Points (Marks < 40%)",
            "",
            "4.2 Key Administrative Contacts:",
            "Dean of Academic Affairs: dean_academic@gbpiet.ac.in | Office: Admin Block Room 204",
            "Chief Proctor: proctor@gbpiet.ac.in | Office: Security Wing",
            "Head of Computer Science & Engineering: cse_hod@gbpiet.ac.in | Office: CS Block Room 102",
            "Training & Placement Officer: tpo@gbpiet.ac.in | Office: T&P Cell"
        ]
    ]

    # Generate PDF Objects
    objects = []
    
    # 1 0 obj: Catalog
    catalog_id = 1
    # 2 0 obj: Pages
    pages_id = 2
    
    page_ids = []
    content_ids = []
    current_id = 3
    
    for _ in pages_content:
        page_ids.append(current_id)
        content_ids.append(current_id + 1)
        current_id += 2

    font_id = current_id

    # Font Object
    font_obj = f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"

    # Pages Object
    kids_str = " ".join([f"{pid} 0 R" for pid in page_ids])
    pages_obj = f"{pages_id} 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>\nendobj"

    # Catalog Object
    catalog_obj = f"{catalog_id} 0 obj\n<< /Type /Catalog /Pages {pages_id} 0 R >>\nendobj"

    page_objects = []
    stream_objects = []

    for idx, lines in enumerate(pages_content):
        p_id = page_ids[idx]
        c_id = content_ids[idx]

        # Build text stream
        text_stream = ["BT", f"/F1 12 Tf", "50 750 Td", "16 TL"]
        for line in lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if line.startswith("SECTION") or line.startswith("GBPIET"):
                text_stream.append(f"/F1 14 Tf")
                text_stream.append(f"({escaped}) Tj T*")
                text_stream.append(f"/F1 11 Tf")
            else:
                text_stream.append(f"({escaped}) Tj T*")
        text_stream.append("ET")
        
        stream_data = "\n".join(text_stream)
        stream_len = len(stream_data)

        # Content Stream Object
        stream_obj = f"{c_id} 0 obj\n<< /Length {stream_len} >>\nstream\n{stream_data}\nendstream\nendobj"
        stream_objects.append(stream_obj)

        # Page Object
        page_obj = (
            f"{p_id} 0 obj\n"
            f"<< /Type /Page /Parent {pages_id} 0 R\n"
            f"   /MediaBox [0 0 612 792]\n"
            f"   /Contents {c_id} 0 R\n"
            f"   /Resources << /Font << /F1 {font_id} 0 R >> >>\n"
            f">>\nendobj"
        )
        page_objects.append(page_obj)

    # Assemble all objects in order
    all_objs = [catalog_obj, pages_obj]
    for p_obj, s_obj in zip(page_objects, stream_objects):
        all_objs.append(p_obj)
        all_objs.append(s_obj)
    all_objs.append(font_obj)

    # Build PDF with xref table
    pdf_header = "%PDF-1.4\n"
    offsets = []
    current_offset = len(pdf_header.encode("latin1"))

    body_parts = []
    for obj_str in all_objs:
        offsets.append(current_offset)
        obj_bytes = (obj_str + "\n").encode("latin1")
        body_parts.append(obj_bytes)
        current_offset += len(obj_bytes)

    xref_offset = current_offset
    xref_str = f"xref\n0 {len(all_objs) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref_str += f"{off:010d} 00000 n \n"

    trailer_str = (
        f"trailer\n"
        f"<< /Size {len(all_objs) + 1}\n"
        f"   /Root {catalog_id} 0 R\n"
        f">>\n"
        f"startxref\n"
        f"{xref_offset}\n"
        f"%%EOF\n"
    )

    with open(output_path, "wb") as f:
        f.write(pdf_header.encode("latin1"))
        for part in body_parts:
            f.write(part)
        f.write(xref_str.encode("latin1"))
        f.write(trailer_str.encode("latin1"))

    print(f"Generated campus sample handbook at: {output_path}")

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent / "data" / "uploads"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "gbpiet_campus_handbook_2026.pdf"
    create_pdf(out_file)
