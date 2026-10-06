import os

filepath = 'c:/TRY-FIT/server.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace get_catalog_html_by_category definition and query
old_def = '''    def get_catalog_html_by_category(self, categories, limit=None, is_guest=False, user=None):
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                format_strings = ','.join(['%s'] * len(categories))
                query = f"SELECT * FROM clothes WHERE category IN ({format_strings}) ORDER BY id ASC"
                if limit is not None:
                    query += f" LIMIT {int(limit)}"
                cursor.execute(query, tuple(categories))
                items = cursor.fetchall()'''

new_def = '''    def get_catalog_html_by_category(self, categories, keyword=None, limit=None, is_guest=False, user=None):
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                format_strings = ','.join(['%s'] * len(categories))
                query = f"SELECT * FROM clothes WHERE category IN ({format_strings})"
                params = list(categories)
                if keyword:
                    query += " AND name LIKE %s"
                    params.append(f"%{keyword}%")
                query += " ORDER BY id ASC"
                if limit is not None:
                    query += f" LIMIT {int(limit)}"
                cursor.execute(query, tuple(params))
                items = cursor.fetchall()'''

content = content.replace(old_def, new_def)

# Replace replace_category_placeholders caller
old_caller = '''        # Determine the HTML to inject
        if active_category in cat_map:
            catalog_html = self.get_catalog_html_by_category(cat_map[active_category], limit=limit, is_guest=is_guest, user=user)'''

new_caller = '''        keyword_map = {
            'shirts': 'Shirt',
            'jackets': 'Jacket',
            'jeans': 'Jean',
            'shoes': 'Shoe',
            'dresses': 'Dress',
            'handbags': 'Handbag'
        }
        keyword = keyword_map.get(active_category)

        # Determine the HTML to inject
        if active_category in cat_map:
            catalog_html = self.get_catalog_html_by_category(cat_map[active_category], keyword=keyword, limit=limit, is_guest=is_guest, user=user)'''

content = content.replace(old_caller, new_caller)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Update successful')
