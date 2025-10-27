#!/usr/bin/env python3
"""
Generate a comprehensive codebook PDF for the dual-engine screening results CSV.
"""

import pandas as pd
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

def create_codebook_pdf(csv_file, output_file=None):
    """Generate a comprehensive codebook PDF for the dual-engine CSV."""
    
    # Generate output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"docs/Dual_Engine_Screening_Codebook_{timestamp}.pdf"
    
    # Create docs directory if it doesn't exist
    os.makedirs("docs", exist_ok=True)
    
    # Load CSV to get column information
    print("📖 Loading CSV file to analyze structure...")
    df = pd.read_csv(csv_file, nrows=5)  # Just load a few rows to get column info
    
    # Create PDF document
    doc = SimpleDocTemplate(output_file, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Build story (content)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=24,
        textColor=colors.darkblue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=16,
        textColor=colors.darkgreen
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Title page
    story.append(Paragraph("Dual-Engine Paper Screening Results", title_style))
    story.append(Paragraph("Comprehensive Codebook", title_style))
    story.append(Spacer(1, 30))
    
    # Metadata table
    metadata_data = [
        ['Document Type:', 'Codebook for CSV Data File'],
        ['Generated:', datetime.now().strftime("%B %d, %Y at %H:%M")],
        ['CSV File:', os.path.basename(csv_file)],
        ['Total Records:', f"{len(pd.read_csv(csv_file)):,} papers"],
        ['Total Columns:', f"{len(df.columns)} variables"],
        ['Screening System:', 'Dual-Engine AI Screening Pipeline'],
        ['Engine 1:', 'Claude Haiku 4.5 (Anthropic)'],
        ['Engine 2:', 'Gemini 2.5 Flash (Google)']
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    
    story.append(metadata_table)
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", heading_style))
    toc_data = [
        "1. Overview and Purpose",
        "2. Data Collection Methodology", 
        "3. Variable Definitions",
        "4. Data Quality and Validation",
        "5. Usage Guidelines",
        "6. Technical Specifications"
    ]
    
    for item in toc_data:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(PageBreak())
    
    # 1. Overview and Purpose
    story.append(Paragraph("1. Overview and Purpose", heading_style))
    
    overview_text = """
    This codebook documents the structure and content of the dual-engine paper screening results dataset. 
    The data represents a comprehensive screening of 12,394 academic papers using two independent AI engines 
    to assess eligibility for systematic review inclusion based on predefined criteria.
    
    The screening process employed a rigorous dual-engine approach to enhance reliability and identify 
    potential disagreements requiring human review. Each paper was independently evaluated by both engines 
    using identical screening criteria, allowing for comprehensive agreement analysis and quality assurance.
    """
    story.append(Paragraph(overview_text, body_style))
    
    # 2. Data Collection Methodology  
    story.append(Paragraph("2. Data Collection Methodology", heading_style))
    
    methodology_text = """
    <b>Screening Engines:</b><br/>
    • Engine 1: Claude Haiku 4.5 (Anthropic) - More conservative approach<br/>
    • Engine 2: Gemini 2.5 Flash (Google) - More decisive approach<br/><br/>
    
    <b>Processing Architecture:</b><br/>
    • Batch-parallel processing with 4 concurrent workers<br/>
    • Batch size of 5 papers per worker cycle<br/>
    • Checkpoint system for session recovery<br/>
    • Total processing time: 5.2 hours<br/><br/>
    
    <b>Screening Criteria:</b><br/>
    Six core eligibility criteria were evaluated for each paper:<br/>
    1. Participants from Low/Middle-Income Countries<br/>
    2. Component A: Cash support provision<br/>
    3. Component B: Productive asset transfers<br/>
    4. Relevant economic/livelihood outcomes<br/>
    5. Appropriate quantitative study design<br/>
    6. Publication year 2004 or later<br/>
    7. Completed study status
    """
    story.append(Paragraph(methodology_text, body_style))
    
    # 3. Variable Definitions
    story.append(Paragraph("3. Variable Definitions", heading_style))
    
    # Group columns by category
    column_groups = {
        "Paper Identification": [
            ("item_id", "Unique paper identifier from original RIS file U1 field", "Text", "121342757"),
            ("paper_id", "Internal processing identifier", "Text", "2023_3117")
        ],
        
        "Paper Metadata": [
            ("title", "Full paper title (cleaned for CSV compatibility)", "Text", "Climate change, income sources..."),
            ("authors", "Author names separated by semicolons", "Text", "Smith J; Jones A"),
            ("journal", "Publication venue or journal name", "Text", "Journal of Development Economics"),
            ("year", "Publication year", "Numeric", "2023"),
            ("doi", "Digital Object Identifier", "Text", "10.1016/j.jdeveco.2023.102956"),
            ("abstract", "Paper abstract (cleaned, whitespace normalized)", "Text", "This study examines...")
        ],
        
        "Engine 1 Results (Claude Haiku 4.5)": [
            ("engine1_decision", "Final screening decision", "Categorical", "exclude | maybe | include | uncertain"),
            ("engine1_success", "Processing success indicator", "Boolean", "True | False"),
            ("engine1_processing_time", "Processing duration in seconds", "Numeric", "5.87"),
            ("engine1_reasoning", "Decision explanation and logic", "Text", "EXCLUDE: 3 criteria marked as NO..."),
            ("engine1_error", "Error message if processing failed", "Text", "API timeout error")
        ],
        
        "Engine 2 Results (Gemini 2.5 Flash)": [
            ("engine2_decision", "Final screening decision", "Categorical", "exclude | maybe | include | uncertain"),
            ("engine2_success", "Processing success indicator", "Boolean", "True | False"), 
            ("engine2_processing_time", "Processing duration in seconds", "Numeric", "2.54"),
            ("engine2_reasoning", "Decision explanation and logic", "Text", "EXCLUDE: 2 criteria marked as NO..."),
            ("engine2_error", "Error message if processing failed", "Text", "Model unavailable")
        ],
        
        "Agreement Analysis": [
            ("both_engines_successful", "Both engines processed successfully", "Boolean", "True | False"),
            ("agreement", "Engines reached same decision", "Boolean", "True | False"),
            ("needs_human_review", "Requires manual review", "Boolean", "True | False"),
            ("consensus_decision", "Final consensus or disagreement status", "Categorical", "exclude | maybe | include | DISAGREEMENT | ERROR"),
            ("review_priority", "Priority level for human review", "Categorical", "LOW - CONSENSUS | MEDIUM - DISAGREEMENT | HIGH - DISAGREEMENT")
        ],
        
        "Processing Metadata": [
            ("worker_id", "Processing worker identifier", "Numeric", "1 | 2 | 3 | 4"),
            ("processed_at", "Processing timestamp (ISO format)", "DateTime", "2025-10-25T01:54:57.235571"),
            ("processing_order", "Order of processing within dataset", "Numeric", "1, 2, 3..."),
            ("faster_engine", "Which engine processed faster", "Text", "Engine 1 | Engine 2"),
            ("speed_difference_seconds", "Time difference between engines", "Numeric", "3.33")
        ]
    }
    
    # Add detailed criteria columns
    criteria_names = [
        "participants_lmic",
        "component_a_cash_support", 
        "component_b_productive_assets",
        "relevant_outcomes",
        "appropriate_study_design",
        "publication_year_2004_plus",
        "completed_study"
    ]
    
    engine1_criteria = []
    engine2_criteria = []
    
    for criterion in criteria_names:
        engine1_criteria.extend([
            (f"engine1_{criterion}_assessment", f"Engine 1 assessment for {criterion.replace('_', ' ')}", "Categorical", "YES | NO | UNCLEAR"),
            (f"engine1_{criterion}_reasoning", f"Engine 1 reasoning for {criterion.replace('_', ' ')}", "Text", "Study explicitly focuses on...")
        ])
        
        engine2_criteria.extend([
            (f"engine2_{criterion}_assessment", f"Engine 2 assessment for {criterion.replace('_', ' ')}", "Categorical", "YES | NO | UNCLEAR"),
            (f"engine2_{criterion}_reasoning", f"Engine 2 reasoning for {criterion.replace('_', ' ')}", "Text", "The abstract states...")
        ])
    
    column_groups["Engine 1 Detailed Criteria"] = engine1_criteria
    column_groups["Engine 2 Detailed Criteria"] = engine2_criteria
    
    # Create variable definition tables
    for group_name, columns in column_groups.items():
        story.append(Paragraph(group_name, subheading_style))
        
        # Create table data
        table_data = [['Variable Name', 'Description', 'Type', 'Example Values']]
        
        for var_name, description, var_type, example in columns:
            # Wrap long text
            wrapped_desc = description[:60] + "..." if len(description) > 60 else description
            wrapped_example = example[:40] + "..." if len(example) > 40 else example
            
            table_data.append([
                var_name,
                wrapped_desc,
                var_type,
                wrapped_example
            ])
        
        # Create and style table
        col_widths = [1.5*inch, 2.5*inch, 0.8*inch, 1.5*inch]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Data styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            
            # Grid and alignment
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
    
    # 4. Data Quality and Validation
    story.append(PageBreak())
    story.append(Paragraph("4. Data Quality and Validation", heading_style))
    
    quality_text = """
    <b>Processing Success Rates:</b><br/>
    • Both engines successful: 100% (12,394/12,394 papers)<br/>
    • Zero processing failures or errors<br/><br/>
    
    <b>Agreement Analysis:</b><br/>
    • Overall agreement rate: 93.0% (11,522/12,394 papers)<br/>
    • Disagreement rate: 7.0% (872/12,394 papers)<br/>
    • All disagreements flagged for human review<br/><br/>
    
    <b>Decision Distribution:</b><br/>
    Engine 1 (Claude Haiku 4.5):<br/>
    • Exclude: 89.1% (11,047 papers)<br/>
    • Maybe: 5.4% (674 papers)<br/>
    • Include: 5.4% (671 papers)<br/>
    • Uncertain: <0.1% (2 papers)<br/><br/>
    
    Engine 2 (Gemini 2.5 Flash):<br/>
    • Exclude: 94.6% (11,723 papers)<br/>
    • Maybe: 3.2% (391 papers)<br/>
    • Include: 2.3% (280 papers)<br/><br/>
    
    <b>Performance Metrics:</b><br/>
    • Average processing speed: 39.6 papers/minute<br/>
    • Engine 1 average time: 5.8 seconds/paper<br/>
    • Engine 2 average time: 3.0 seconds/paper<br/>
    • Estimated human review time: 436 hours for disagreements
    """
    story.append(Paragraph(quality_text, body_style))
    
    # 5. Usage Guidelines
    story.append(Paragraph("5. Usage Guidelines", heading_style))
    
    usage_text = """
    <b>Primary Analysis Variables:</b><br/>
    • Use 'consensus_decision' for papers with agreement<br/>
    • Filter 'needs_human_review = True' for manual review queue<br/>
    • Use 'review_priority' to prioritize human review workload<br/><br/>
    
    <b>Quality Assurance:</b><br/>
    • Check 'both_engines_successful' before analysis<br/>
    • Review 'engine1_error' and 'engine2_error' for processing issues<br/>
    • Validate reasoning chains in detailed criteria columns<br/><br/>
    
    <b>Statistical Analysis:</b><br/>
    • Agreement analysis: Use 'agreement' and engine-specific decisions<br/>
    • Performance comparison: Use processing time variables<br/>
    • Criteria analysis: Use detailed assessment columns<br/><br/>
    
    <b>Data Limitations:</b><br/>
    • Text fields cleaned for CSV compatibility (quotes removed, whitespace normalized)<br/>
    • U1 matching achieved 100% success rate with title-based mapping<br/>
    • Processing order may not reflect original dataset sequence
    """
    story.append(Paragraph(usage_text, body_style))
    
    # 6. Technical Specifications
    story.append(Paragraph("6. Technical Specifications", heading_style))
    
    tech_text = """
    <b>File Format:</b><br/>
    • CSV with comma separation<br/>
    • UTF-8 encoding<br/>
    • Proper quoting for text fields<br/>
    • Header row included<br/><br/>
    
    <b>Missing Data Handling:</b><br/>
    • Empty strings for missing text values<br/>
    • False for missing boolean values<br/>
    • 0 for missing numeric values<br/><br/>
    
    <b>Data Types:</b><br/>
    • Text: String values, cleaned and normalized<br/>
    • Boolean: True/False values<br/>
    • Numeric: Integer or decimal values<br/>
    • Categorical: Fixed set of predefined values<br/>
    • DateTime: ISO format timestamps<br/><br/>
    
    <b>Version Information:</b><br/>
    • Generation Date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """<br/>
    • Source System: Dual-Engine AI Screening Pipeline v2.0<br/>
    • Processing Session: batch_dual_screening_20251025_014003
    """
    story.append(Paragraph(tech_text, body_style))
    
    # Build PDF
    print(f"📄 Generating PDF codebook: {output_file}")
    doc.build(story)
    
    print(f"\n✅ Codebook PDF created successfully!")
    print(f"   📄 File: {output_file}")
    print(f"   📊 Pages: ~15-20 pages")
    print(f"   🔍 Content: Complete variable documentation")
    
    return output_file

def main():
    import sys
    
    # Default to the latest CSV file
    csv_file = "data/output/dual_engine_results_with_u1_20251026_175742.csv"
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ ERROR: CSV file not found: {csv_file}")
        print("Usage: python generate_codebook.py [csv_file_path]")
        sys.exit(1)
    
    print("📚 DUAL-ENGINE SCREENING CODEBOOK GENERATOR")
    print("=" * 50)
    
    codebook_file = create_codebook_pdf(csv_file)
    
    print(f"\n📖 Codebook ready for use!")

if __name__ == "__main__":
    main()