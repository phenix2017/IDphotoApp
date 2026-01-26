#!/usr/bin/env python3
"""Streamlit GUI for IDphotoApp - Interactive photo processing interface."""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io
import tempfile

from process_photo import (
    load_specs,
    detect_face,
    crop_to_spec,
    replace_background,
    build_print_sheet,
    LayoutSpec,
    parse_layout,
)

# Configure page
st.set_page_config(
    page_title="ID Photo Processor",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📸 ID Photo Processor")
st.markdown("Auto-crop and process identity photos for passport compliance")

# Load specs
specs = load_specs(Path("specs.json"))

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    
    # Country selection
    country = st.selectbox(
        "Select Country",
        options=list(specs.keys()),
        format_func=lambda x: f"{x} - {specs[x].name}",
        help="Choose the country specification for your ID photo"
    )
    
    # Photo settings
    st.subheader("Photo Settings")
    replace_bg = st.checkbox("Replace Background", value=False)
    dpi = st.slider("DPI (Quality)", min_value=100, max_value=600, value=300, step=50)
    
    # Layout settings
    st.subheader("Print Layout")
    layout_preset = st.radio("Layout Size", ["4x6", "6x6", "Custom"])
    
    if layout_preset == "Custom":
        layout_w = st.number_input("Width (inches)", value=4.0, min_value=1.0, step=0.5)
        layout_h = st.number_input("Height (inches)", value=6.0, min_value=1.0, step=0.5)
        layout = LayoutSpec(width_in=layout_w, height_in=layout_h)
    else:
        layout = parse_layout(layout_preset)
    
    copies = st.slider("Number of Copies", min_value=1, max_value=20, value=6)
    margin = st.number_input("Margin (inches)", value=0.1, min_value=0.0, step=0.05)
    spacing = st.number_input("Spacing (inches)", value=0.1, min_value=0.0, step=0.05)

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Photo")
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png"],
        help="Upload a clear, front-facing photo"
    )

with col2:
    st.subheader("Photo Info")
    if uploaded_file:
        st.info(f"📁 File: {uploaded_file.name}")
        st.info(f"📏 Size: {uploaded_file.size:,} bytes")

# Process photo if uploaded
if uploaded_file:
    try:
        # Read the uploaded image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image_bgr is None:
            st.error("❌ Could not read image. Please upload a valid image file.")
        else:
            with st.spinner("Processing..."):
                # Replace background if selected
                if replace_bg:
                    image_bgr = replace_background(image_bgr, specs[country].background_rgb)
                
                # Detect face
                bbox, eye_point = detect_face(image_bgr)
                
                # Crop to spec
                cropped_bgr = crop_to_spec(image_bgr, bbox, eye_point, specs[country], dpi)
                
                # Convert to RGB for display
                cropped_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
                cropped_pil = Image.fromarray(cropped_rgb)
                
                # Generate print sheet
                sheet = build_print_sheet(
                    photo=cropped_pil,
                    layout=layout,
                    dpi=dpi,
                    margin_in=margin,
                    spacing_in=spacing,
                    copies=copies,
                )
            
            # Display results
            st.success("✅ Photo processed successfully!")
            
            col_photo, col_sheet = st.columns(2)
            
            with col_photo:
                st.subheader("Cropped Photo")
                spec = specs[country]
                w_in, h_in = spec.width_in, spec.height_in
                st.image(cropped_pil, caption=f"{w_in}\" × {h_in}\"", use_column_width=True)
                
                # Photo size info
                w_px, h_px = cropped_pil.size
                st.caption(f"Size: {w_px} × {h_px} pixels @ {dpi} DPI")
                
                # Download cropped photo
                img_buffer = io.BytesIO()
                cropped_pil.save(img_buffer, format="JPEG", quality=95)
                img_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Photo",
                    data=img_buffer,
                    file_name=f"{country.lower()}_photo.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            with col_sheet:
                st.subheader("Print Sheet")
                st.image(sheet, caption=f"Print Layout: {layout.width_in}\" × {layout.height_in}\"", use_column_width=True)
                
                # Sheet size info
                sheet_w, sheet_h = sheet.size
                st.caption(f"Sheet: {sheet_w} × {sheet_h} pixels @ {dpi} DPI\n{copies} copies")
                
                # Download print sheet
                sheet_buffer = io.BytesIO()
                sheet.save(sheet_buffer, format="JPEG", quality=95)
                sheet_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Sheet",
                    data=sheet_buffer,
                    file_name=f"{country.lower()}_sheet_{int(layout.width_in)}x{int(layout.height_in)}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            # Specifications display
            st.subheader("Specifications Used")
            col_specs1, col_specs2, col_specs3 = st.columns(3)
            
            with col_specs1:
                st.metric("Country", f"{country} - {specs[country].name}")
            
            with col_specs2:
                st.metric("Photo Size", f"{specs[country].width_in}\" × {specs[country].height_in}\"")
            
            with col_specs3:
                st.metric("Head Height Ratio", f"{specs[country].head_height_ratio:.0%}")
    
    except RuntimeError as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Try: Clear photo, good lighting, front-facing pose")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.info("📝 Please check that your image is valid and properly formatted")

# Instructions sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("📖 How to Use")
    with st.expander("Setup", expanded=False):
        st.markdown("""
        1. Select your country
        2. Configure settings (DPI, layout, etc.)
        3. Upload a photo
        4. Download the results
        """)
    
    with st.expander("Tips for Best Results", expanded=False):
        st.markdown("""
        - **Lighting**: Bright, even lighting
        - **Pose**: Look straight at camera
        - **Expression**: Neutral, mouth closed
        - **Background**: Plain, uniform color
        - **File Format**: JPEG or PNG
        - **Resolution**: At least 640×480 pixels
        """)
    
    with st.expander("About Countries", expanded=False):
        for code, spec in specs.items():
            st.write(f"**{code}** - {spec.name}")
            st.write(f"Size: {spec.width_in}\" × {spec.height_in}\"")
