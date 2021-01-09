#
# Source this to activate the correct virtual environment.
#     ~/preview-site/bin/active for the preview site.
#     ~/production-site/bin/active for the production site.
#
SITE_DIR=$(dirname "${PWD}")
SITE_TYPE=$(basename "${SITE_DIR}")
unset SITE_DIR

source ~/"${SITE_TYPE}"-site/bin/activate
