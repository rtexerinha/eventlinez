#!/usr/bin/env python
"""
Script to fix the migration issue with sales_by_vendor view
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventlinez.settings')
django.setup()

from django.db import connection

def fix_sales_by_vendor_view():
    """Drop and recreate the sales_by_vendor view to fix migration issues"""
    with connection.cursor() as cursor:
        print("Checking if sales_by_vendor view exists...")

        # Check if view exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.views 
                WHERE table_name = 'sales_by_vendor'
            );
        """)

        view_exists = cursor.fetchone()[0]

        if view_exists:
            print("Dropping sales_by_vendor view...")
            cursor.execute("DROP VIEW IF EXISTS sales_by_vendor CASCADE;")
            print("✓ View dropped successfully")
        else:
            print("View does not exist, skipping drop")

        print("Creating sales_by_vendor view...")

        # Recreate the view with proper structure
        create_view_sql = """
        CREATE OR REPLACE VIEW sales_by_vendor AS
        SELECT 
            ROW_NUMBER() OVER (ORDER BY v.id, e.id) as id,
            v.id as vendor_id,
            e.id as event_id,
            COALESCE(SUM(oi.quantity), 0) as qty,
            COALESCE(SUM(oi.amount), 0) as amount
        FROM promoter_vendor v
        CROSS JOIN event_event e
        LEFT JOIN order_orderitem oi ON oi.vendor_id = v.id 
            AND oi.event_ticket_id IN (
                SELECT id FROM event_ticket WHERE event_id = e.id
            )
        GROUP BY v.id, e.id;
        """

        cursor.execute(create_view_sql)
        print("✓ View created successfully")

if __name__ == "__main__":
    print("Fixing sales_by_vendor view migration issue...")
    fix_sales_by_vendor_view()
    print("Done!")
