app_name = "stocker"
app_title = "Stocker"
app_publisher = "asithara@htsqatar.com"
app_description = "stocker"
app_email = "asithara@htsqatar.com"
app_license = "mit"


doctype_js = {
    "Stock Reconciliation": "public/js/stock_reconciliation_custom.js"
}


doc_events = {
    # "Employee": {
    #     "on_update": "stocker.stocker.api.create_qr_code",}
    "Stock Reconciliation": {
        "on_submit": "stocker.stocker.api.on_submit"
    }
}



fixtures = [
    {"dt": "Custom Field", "filters": {"module": "Stocker"}},
    {
        "dt": "Client Script",
        "filters": {"module": "Stocker"},
    },
]
# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"stocker.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

