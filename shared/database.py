"""
Supabase client setup.

WHY two clients?
- supabase_anon: Uses the "anon" key. Supabase Row-Level Security (RLS) is enforced.
  Good for client-facing queries where you want the database to double-check permissions.
- supabase_admin: Uses the "service_role" key. BYPASSES all RLS policies.
  Good for server-side operations where your code already verified permissions
  (e.g., after checking JWT + role in a FastAPI dependency).

WHY use admin as default?
Our services already authenticate users via JWT and filter by user_id in every query.
RLS would be redundant and adds complexity. The service_role client lets us insert/update
without writing RLS policies for every table. This is the same pattern used in the Infinity project.

IMPORTANT: Never expose the service_role key to the frontend or any client-side code.
"""

from supabase import Client, create_client

from shared.config import settings


def get_supabase_client() -> Client:
    """Return Supabase client using anon key (RLS enforced)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_admin() -> Client:
    """Return Supabase client using service key (bypasses RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


# Module-level singletons -- created once when the module is first imported.
# WHY singletons? Creating a Supabase client is cheap but establishing the
# underlying HTTP connection pool takes time. Reusing one client per process
# is the standard pattern.
supabase_anon: Client = get_supabase_client()
supabase_admin: Client = get_supabase_admin()

# Default client for all service-layer queries.
supabase: Client = supabase_admin
