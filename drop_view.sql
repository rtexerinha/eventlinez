-- Drop the sales_by_vendor view that's blocking migrations
DROP VIEW IF EXISTS sales_by_vendor CASCADE;

-- Also drop any other views or rules that might depend on it
DROP VIEW IF EXISTS public.sales_by_vendor CASCADE;

-- Show remaining views to verify
SELECT schemaname, viewname FROM pg_views WHERE schemaname = 'public';
