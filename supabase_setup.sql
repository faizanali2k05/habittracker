-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Create tables
create table if not exists users (
  id uuid primary key references auth.users(id),
  email text unique,
  role text default 'user'
);

create table if not exists categories (
  id uuid primary key default uuid_generate_v4(),
  name text,
  user_id uuid references auth.users(id)
);

create table if not exists tasks (
  id uuid primary key default uuid_generate_v4(),
  title text,
  description text,
  due_date date,
  priority text,
  status text default 'pending',
  user_id uuid references auth.users(id),
  category_id uuid references categories(id)
);

create table if not exists habits (
  id uuid primary key default uuid_generate_v4(),
  name text,
  frequency text,
  reminder_time time,
  user_id uuid references auth.users(id)
);

create table if not exists habit_logs (
  id uuid primary key default uuid_generate_v4(),
  habit_id uuid references habits(id),
  completed_date date,
  user_id uuid references auth.users(id)
);

-- Enable Row Level Security
alter table users enable row level security;
alter table categories enable row level security;
alter table tasks enable row level security;
alter table habits enable row level security;
alter table habit_logs enable row level security;

-- Create Policies

-- Users: Allow users to select, insert, update, delete their own profile
-- ID must match the auth.uid()
create policy "Users can manage their own profile" on users
  for all using (auth.uid() = id) with check (auth.uid() = id);

-- Categories
create policy "Users can manage their own categories" on categories
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Tasks
create policy "Users can manage their own tasks" on tasks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Habits
create policy "Users can manage their own habits" on habits
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Habit Logs
create policy "Users can manage their own habit logs" on habit_logs
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  
-- Admin Policies (Optional, based on requirement)
create policy "Admins can access all data" on users
  for select using (
    exists (select 1 from users where id = auth.uid() and role = 'admin')
  );
  
-- Allow admins to see tasks, etc? 
-- The user asked for "Admin can access all data on tasks"
create policy "Admins can access all tasks" on tasks
  for all using (
    exists (select 1 from users where id = auth.uid() and role = 'admin')
  );
