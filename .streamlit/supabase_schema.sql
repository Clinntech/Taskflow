-- =========================================================
-- TASKFLOW SUPABASE DATABASE SCHEMA
-- =========================================================


-- =========================================================
-- 1. ENABLE UUID SUPPORT
-- =========================================================

create extension if not exists pgcrypto;


-- =========================================================
-- 2. TASKS TABLE
-- =========================================================

create table if not exists public.tasks (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null default auth.uid()
        references auth.users(id)
        on delete cascade,

    title text not null
        check (char_length(trim(title)) between 1 and 150),

    description text not null default '',

    due_date date not null,

    priority text not null default 'Medium'
        check (priority in ('Low', 'Medium', 'High')),

    completed boolean not null default false,

    completed_at timestamptz,

    created_at timestamptz not null default now(),

    updated_at timestamptz not null default now()
);


-- =========================================================
-- 3. WEEKLY GOALS TABLE
-- =========================================================

create table if not exists public.weekly_goals (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null default auth.uid()
        references auth.users(id)
        on delete cascade,

    title text not null
        check (char_length(trim(title)) between 1 and 150),

    description text not null default '',

    week_start date not null,

    target_date date,

    completed boolean not null default false,

    completed_at timestamptz,

    created_at timestamptz not null default now(),

    updated_at timestamptz not null default now(),

    constraint target_date_within_goal_week
        check (
            target_date is null
            or target_date between week_start and week_start + 6
        )
);


-- =========================================================
-- 4. INDEXES
-- =========================================================

create index if not exists tasks_user_id_index
    on public.tasks(user_id);

create index if not exists tasks_user_due_date_index
    on public.tasks(user_id, due_date);

create index if not exists tasks_user_completed_index
    on public.tasks(user_id, completed);

create index if not exists weekly_goals_user_id_index
    on public.weekly_goals(user_id);

create index if not exists weekly_goals_user_week_index
    on public.weekly_goals(user_id, week_start);

create index if not exists weekly_goals_user_completed_index
    on public.weekly_goals(user_id, completed);


-- =========================================================
-- 5. AUTOMATIC UPDATED_AT FUNCTION
-- =========================================================

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


-- =========================================================
-- 6. UPDATED_AT TRIGGERS
-- =========================================================

drop trigger if exists set_tasks_updated_at
on public.tasks;

create trigger set_tasks_updated_at
before update on public.tasks
for each row
execute function public.set_updated_at();


drop trigger if exists set_weekly_goals_updated_at
on public.weekly_goals;

create trigger set_weekly_goals_updated_at
before update on public.weekly_goals
for each row
execute function public.set_updated_at();


-- =========================================================
-- 7. COMPLETION TIMESTAMP FUNCTION
-- =========================================================

create or replace function public.set_completion_timestamp()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
    if new.completed = true and old.completed = false then
        new.completed_at = now();
    elsif new.completed = false then
        new.completed_at = null;
    end if;

    return new;
end;
$$;


-- =========================================================
-- 8. COMPLETION TIMESTAMP TRIGGERS
-- =========================================================

drop trigger if exists set_task_completion_timestamp
on public.tasks;

create trigger set_task_completion_timestamp
before update of completed on public.tasks
for each row
execute function public.set_completion_timestamp();


drop trigger if exists set_goal_completion_timestamp
on public.weekly_goals;

create trigger set_goal_completion_timestamp
before update of completed on public.weekly_goals
for each row
execute function public.set_completion_timestamp();


-- =========================================================
-- 9. ENABLE ROW LEVEL SECURITY
-- =========================================================

alter table public.tasks enable row level security;
alter table public.weekly_goals enable row level security;


-- =========================================================
-- 10. REMOVE OLD TASK POLICIES
-- =========================================================

drop policy if exists "Users can view their own tasks"
on public.tasks;

drop policy if exists "Users can create their own tasks"
on public.tasks;

drop policy if exists "Users can update their own tasks"
on public.tasks;

drop policy if exists "Users can delete their own tasks"
on public.tasks;


-- =========================================================
-- 11. TASK SECURITY POLICIES
-- =========================================================

create policy "Users can view their own tasks"
on public.tasks
for select
to authenticated
using (
    (select auth.uid()) = user_id
);


create policy "Users can create their own tasks"
on public.tasks
for insert
to authenticated
with check (
    (select auth.uid()) = user_id
);


create policy "Users can update their own tasks"
on public.tasks
for update
to authenticated
using (
    (select auth.uid()) = user_id
)
with check (
    (select auth.uid()) = user_id
);


create policy "Users can delete their own tasks"
on public.tasks
for delete
to authenticated
using (
    (select auth.uid()) = user_id
);


-- =========================================================
-- 12. REMOVE OLD WEEKLY GOAL POLICIES
-- =========================================================

drop policy if exists "Users can view their own weekly goals"
on public.weekly_goals;

drop policy if exists "Users can create their own weekly goals"
on public.weekly_goals;

drop policy if exists "Users can update their own weekly goals"
on public.weekly_goals;

drop policy if exists "Users can delete their own weekly goals"
on public.weekly_goals;


-- =========================================================
-- 13. WEEKLY GOAL SECURITY POLICIES
-- =========================================================

create policy "Users can view their own weekly goals"
on public.weekly_goals
for select
to authenticated
using (
    (select auth.uid()) = user_id
);


create policy "Users can create their own weekly goals"
on public.weekly_goals
for insert
to authenticated
with check (
    (select auth.uid()) = user_id
);


create policy "Users can update their own weekly goals"
on public.weekly_goals
for update
to authenticated
using (
    (select auth.uid()) = user_id
)
with check (
    (select auth.uid()) = user_id
);


create policy "Users can delete their own weekly goals"
on public.weekly_goals
for delete
to authenticated
using (
    (select auth.uid()) = user_id
);


-- =========================================================
-- 14. TABLE PERMISSIONS
-- =========================================================

revoke all on table public.tasks from anon;
revoke all on table public.weekly_goals from anon;

grant select, insert, update, delete
on table public.tasks
to authenticated;

grant select, insert, update, delete
on table public.weekly_goals
to authenticated;

