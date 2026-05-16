## 2024-05-24 - Added visual required indicators
**Learning:** Gradio UI forms can easily lack visual required indicators, causing frustration when Pydantic backends enforce missing field validations later on submission.
**Action:** When building or updating Gradio applications, always add `info="Required"` to `gr.Textbox`, `gr.Dropdown` and other inputs corresponding to mandatory fields in underlying Pydantic schemas.
