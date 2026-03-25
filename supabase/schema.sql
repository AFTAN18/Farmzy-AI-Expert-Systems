-- FARMZY Supabase Schema
-- Run in Supabase SQL editor

create extension if not exists pgcrypto;

create table if not exists public.farms (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  location text,
  latitude float8,
  longitude float8,
  owner_id uuid,
  thingspeak_channel_id text,
  thingspeak_read_api_key text,
  created_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role text not null default 'farmer' check (role in ('farmer', 'agronomist', 'admin')),
  farm_id uuid references public.farms(id) on delete set null,
  created_at timestamptz not null default now()
);

alter table public.farms
  add constraint farms_owner_id_fkey
  foreign key (owner_id) references public.profiles(id) on delete set null;

create table if not exists public.fields (
  id uuid primary key default gen_random_uuid(),
  farm_id uuid not null references public.farms(id) on delete cascade,
  name text not null,
  area_hectares float8,
  current_crop text,
  zone_label text,
  zone_cluster_id int,
  created_at timestamptz not null default now()
);

create table if not exists public.sensor_readings (
  id uuid primary key default gen_random_uuid(),
  field_id uuid not null references public.fields(id) on delete cascade,
  farm_id uuid not null references public.farms(id) on delete cascade,
  thingspeak_entry_id bigint not null,
  recorded_at timestamptz not null,
  nitrogen float8,
  phosphorus float8,
  potassium float8,
  temperature float8,
  humidity float8,
  ph float8,
  gas_ppm float8,
  soil_moisture float8,
  ingested_at timestamptz not null default now(),
  unique (farm_id, thingspeak_entry_id)
);

create index if not exists idx_sensor_readings_farm_recorded_desc
  on public.sensor_readings (farm_id, recorded_at desc);

create index if not exists idx_sensor_readings_field_recorded_desc
  on public.sensor_readings (field_id, recorded_at desc);

create table if not exists public.irrigation_predictions (
  id uuid primary key default gen_random_uuid(),
  field_id uuid not null references public.fields(id) on delete cascade,
  sensor_reading_id uuid not null references public.sensor_readings(id) on delete cascade,
  predicted_at timestamptz not null default now(),
  water_requirement_liters float8,
  irrigation_decision text check (irrigation_decision in ('ON', 'OFF')),
  confidence_score float8,
  model_version text,
  expert_rule_fired text,
  fuzzy_membership_score float8,
  reasoning_trace jsonb not null default '{}'::jsonb
);

create index if not exists idx_irrigation_predictions_field_predicted_desc
  on public.irrigation_predictions (field_id, predicted_at desc);

create table if not exists public.crop_recommendations (
  id uuid primary key default gen_random_uuid(),
  field_id uuid not null references public.fields(id) on delete cascade,
  sensor_reading_id uuid not null references public.sensor_readings(id) on delete cascade,
  recommended_at timestamptz not null default now(),
  top_crop_1 text,
  top_crop_2 text,
  top_crop_3 text,
  probabilities jsonb not null default '{}'::jsonb,
  naive_bayes_confidence float8,
  model_version text,
  reasoning_summary text
);

create index if not exists idx_crop_recommendations_field_recommended_desc
  on public.crop_recommendations (field_id, recommended_at desc);

create table if not exists public.field_zones (
  id uuid primary key default gen_random_uuid(),
  farm_id uuid not null references public.farms(id) on delete cascade,
  run_at timestamptz not null default now(),
  num_clusters int not null,
  cluster_centers jsonb not null default '[]'::jsonb,
  cluster_labels jsonb not null default '{}'::jsonb,
  pca_explained_variance jsonb,
  pca_components jsonb,
  inertia float8,
  model_version text
);

create index if not exists idx_field_zones_farm_run_desc
  on public.field_zones (farm_id, run_at desc);

create table if not exists public.expert_system_rules (
  id uuid primary key default gen_random_uuid(),
  rule_id text not null unique,
  rule_name text not null,
  condition_description text not null,
  action_description text not null,
  priority int not null,
  is_active boolean not null default true,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create index if not exists idx_expert_rules_priority
  on public.expert_system_rules (is_active, priority desc);

create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  farm_id uuid not null references public.farms(id) on delete cascade,
  field_id uuid references public.fields(id) on delete set null,
  alert_type text not null,
  severity text not null check (severity in ('info', 'warning', 'critical')),
  message text not null,
  is_resolved boolean not null default false,
  triggered_at timestamptz not null default now(),
  resolved_at timestamptz
);

create index if not exists idx_alerts_farm_active
  on public.alerts (farm_id, is_resolved, triggered_at desc);

create table if not exists public.model_registry (
  id uuid primary key default gen_random_uuid(),
  model_type text not null check (model_type in ('linear_regression', 'naive_bayes', 'kmeans', 'pca')),
  version text not null,
  accuracy_metric float8,
  metric_name text,
  trained_at timestamptz not null default now(),
  training_rows int,
  artifact_path text,
  is_active boolean not null default true,
  notes text,
  unique(model_type, version)
);

create index if not exists idx_model_registry_active
  on public.model_registry (model_type, is_active, trained_at desc);

create or replace function public.is_admin_or_agronomist()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles p
    where p.id = auth.uid()
      and p.role in ('admin', 'agronomist')
  );
$$;

create or replace function public.is_farm_member(target_farm_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles p
    where p.id = auth.uid()
      and p.farm_id = target_farm_id
  )
  or exists (
    select 1
    from public.farms f
    where f.id = target_farm_id
      and f.owner_id = auth.uid()
  );
$$;

alter table public.profiles enable row level security;
alter table public.farms enable row level security;
alter table public.fields enable row level security;
alter table public.sensor_readings enable row level security;
alter table public.irrigation_predictions enable row level security;
alter table public.crop_recommendations enable row level security;
alter table public.field_zones enable row level security;
alter table public.expert_system_rules enable row level security;
alter table public.alerts enable row level security;
alter table public.model_registry enable row level security;

drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own
on public.profiles
for select
using (id = auth.uid());

drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own
on public.profiles
for update
using (id = auth.uid())
with check (id = auth.uid());

drop policy if exists profiles_insert_own on public.profiles;
create policy profiles_insert_own
on public.profiles
for insert
with check (id = auth.uid());

drop policy if exists farms_owner_all on public.farms;
create policy farms_owner_all
on public.farms
for all
using (owner_id = auth.uid() or auth.role() = 'service_role')
with check (owner_id = auth.uid() or auth.role() = 'service_role');

drop policy if exists farms_members_select on public.farms;
create policy farms_members_select
on public.farms
for select
using (
  owner_id = auth.uid()
  or public.is_farm_member(id)
  or auth.role() = 'service_role'
);

drop policy if exists fields_member_select on public.fields;
create policy fields_member_select
on public.fields
for select
using (public.is_farm_member(farm_id) or auth.role() = 'service_role');

drop policy if exists fields_owner_manage on public.fields;
create policy fields_owner_manage
on public.fields
for all
using (
  auth.role() = 'service_role'
  or exists (
    select 1 from public.farms f where f.id = fields.farm_id and f.owner_id = auth.uid()
  )
)
with check (
  auth.role() = 'service_role'
  or exists (
    select 1 from public.farms f where f.id = fields.farm_id and f.owner_id = auth.uid()
  )
);

drop policy if exists sensor_member_select on public.sensor_readings;
create policy sensor_member_select
on public.sensor_readings
for select
using (public.is_farm_member(farm_id) or auth.role() = 'service_role');

drop policy if exists sensor_service_write on public.sensor_readings;
create policy sensor_service_write
on public.sensor_readings
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists irrigation_member_select on public.irrigation_predictions;
create policy irrigation_member_select
on public.irrigation_predictions
for select
using (
  auth.role() = 'service_role'
  or exists (
    select 1
    from public.fields f
    where f.id = irrigation_predictions.field_id
      and public.is_farm_member(f.farm_id)
  )
);

drop policy if exists irrigation_service_write on public.irrigation_predictions;
create policy irrigation_service_write
on public.irrigation_predictions
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists crop_member_select on public.crop_recommendations;
create policy crop_member_select
on public.crop_recommendations
for select
using (
  auth.role() = 'service_role'
  or exists (
    select 1
    from public.fields f
    where f.id = crop_recommendations.field_id
      and public.is_farm_member(f.farm_id)
  )
);

drop policy if exists crop_service_write on public.crop_recommendations;
create policy crop_service_write
on public.crop_recommendations
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists zones_member_select on public.field_zones;
create policy zones_member_select
on public.field_zones
for select
using (public.is_farm_member(farm_id) or auth.role() = 'service_role');

drop policy if exists zones_service_write on public.field_zones;
create policy zones_service_write
on public.field_zones
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists alerts_member_select on public.alerts;
create policy alerts_member_select
on public.alerts
for select
using (public.is_farm_member(farm_id) or auth.role() = 'service_role');

drop policy if exists alerts_service_write on public.alerts;
create policy alerts_service_write
on public.alerts
for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

drop policy if exists rules_public_select on public.expert_system_rules;
create policy rules_public_select
on public.expert_system_rules
for select
using (auth.uid() is not null or auth.role() = 'service_role');

drop policy if exists rules_manage_admin_agronomist on public.expert_system_rules;
create policy rules_manage_admin_agronomist
on public.expert_system_rules
for all
using (
  auth.role() = 'service_role'
  or public.is_admin_or_agronomist()
)
with check (
  auth.role() = 'service_role'
  or public.is_admin_or_agronomist()
);

drop policy if exists model_registry_select_auth on public.model_registry;
create policy model_registry_select_auth
on public.model_registry
for select
using (auth.uid() is not null or auth.role() = 'service_role');

drop policy if exists model_registry_admin_write on public.model_registry;
create policy model_registry_admin_write
on public.model_registry
for all
using (
  auth.role() = 'service_role'
  or exists (
    select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'
  )
)
with check (
  auth.role() = 'service_role'
  or exists (
    select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'
  )
);

do $$
begin
  begin
    alter publication supabase_realtime add table public.sensor_readings;
  exception when duplicate_object then
    null;
  end;

  begin
    alter publication supabase_realtime add table public.irrigation_predictions;
  exception when duplicate_object then
    null;
  end;

  begin
    alter publication supabase_realtime add table public.alerts;
  exception when duplicate_object then
    null;
  end;
end
$$;

create or replace function public.notify_new_reading()
returns trigger
language plpgsql
as $$
declare
  payload text;
begin
  payload := json_build_object(
    'id', new.id,
    'field_id', new.field_id,
    'farm_id', new.farm_id
  )::text;

  perform pg_notify('new_sensor_data', payload);
  return new;
end;
$$;

drop trigger if exists trg_notify_new_reading on public.sensor_readings;
create trigger trg_notify_new_reading
after insert on public.sensor_readings
for each row
execute function public.notify_new_reading();

create or replace view public.v_latest_readings as
select distinct on (sr.field_id)
  sr.id,
  sr.field_id,
  sr.farm_id,
  sr.thingspeak_entry_id,
  sr.recorded_at,
  sr.nitrogen,
  sr.phosphorus,
  sr.potassium,
  sr.temperature,
  sr.humidity,
  sr.ph,
  sr.gas_ppm,
  sr.soil_moisture,
  sr.ingested_at
from public.sensor_readings sr
order by sr.field_id, sr.recorded_at desc;

create or replace view public.v_field_dashboard as
with latest_pred as (
  select distinct on (ip.field_id)
    ip.field_id,
    ip.id as prediction_id,
    ip.predicted_at,
    ip.water_requirement_liters,
    ip.irrigation_decision,
    ip.confidence_score,
    ip.model_version,
    ip.expert_rule_fired,
    ip.fuzzy_membership_score,
    ip.reasoning_trace
  from public.irrigation_predictions ip
  order by ip.field_id, ip.predicted_at desc
),
latest_crop as (
  select distinct on (cr.field_id)
    cr.field_id,
    cr.id as crop_recommendation_id,
    cr.recommended_at,
    cr.top_crop_1,
    cr.top_crop_2,
    cr.top_crop_3,
    cr.probabilities,
    cr.naive_bayes_confidence,
    cr.model_version as crop_model_version,
    cr.reasoning_summary
  from public.crop_recommendations cr
  order by cr.field_id, cr.recommended_at desc
)
select
  f.id as field_id,
  f.farm_id,
  f.name as field_name,
  f.area_hectares,
  f.current_crop,
  f.zone_label,
  f.zone_cluster_id,
  lr.id as latest_reading_id,
  lr.recorded_at,
  lr.nitrogen,
  lr.phosphorus,
  lr.potassium,
  lr.temperature,
  lr.humidity,
  lr.ph,
  lr.gas_ppm,
  lr.soil_moisture,
  lp.prediction_id,
  lp.predicted_at,
  lp.water_requirement_liters,
  lp.irrigation_decision,
  lp.confidence_score,
  lp.expert_rule_fired,
  lp.fuzzy_membership_score,
  lp.reasoning_trace,
  lc.crop_recommendation_id,
  lc.recommended_at,
  lc.top_crop_1,
  lc.top_crop_2,
  lc.top_crop_3,
  lc.probabilities,
  lc.naive_bayes_confidence,
  lc.reasoning_summary
from public.fields f
left join public.v_latest_readings lr on lr.field_id = f.id
left join latest_pred lp on lp.field_id = f.id
left join latest_crop lc on lc.field_id = f.id;

create or replace view public.v_daily_averages as
select
  sr.farm_id,
  date_trunc('day', sr.recorded_at) as day,
  avg(sr.nitrogen) as avg_nitrogen,
  avg(sr.phosphorus) as avg_phosphorus,
  avg(sr.potassium) as avg_potassium,
  avg(sr.temperature) as avg_temperature,
  avg(sr.humidity) as avg_humidity,
  avg(sr.ph) as avg_ph,
  avg(sr.gas_ppm) as avg_gas_ppm,
  avg(sr.soil_moisture) as avg_soil_moisture,
  count(*) as reading_count
from public.sensor_readings sr
group by sr.farm_id, date_trunc('day', sr.recorded_at)
order by day desc;

insert into public.farms (
  id,
  name,
  location,
  latitude,
  longitude,
  thingspeak_channel_id,
  thingspeak_read_api_key
)
values (
  '11111111-1111-1111-1111-111111111111',
  'FARMZY Demo Farm',
  'Demo Location',
  13.0827,
  80.2707,
  '2972911',
  null
)
on conflict (id) do update
set
  name = excluded.name,
  location = excluded.location,
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  thingspeak_channel_id = excluded.thingspeak_channel_id;

insert into public.fields (
  id,
  farm_id,
  name,
  area_hectares,
  current_crop,
  zone_label,
  zone_cluster_id
)
values
  ('22222222-2222-2222-2222-222222222221', '11111111-1111-1111-1111-111111111111', 'North Plot', 2.5, 'Rice', 'Zone 1', 0),
  ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'South Plot', 3.1, 'Wheat', 'Zone 2', 1),
  ('22222222-2222-2222-2222-222222222223', '11111111-1111-1111-1111-111111111111', 'East Plot', 1.8, 'Maize', 'Zone 3', 2)
on conflict (id) do update
set
  farm_id = excluded.farm_id,
  name = excluded.name,
  area_hectares = excluded.area_hectares,
  current_crop = excluded.current_crop,
  zone_label = excluded.zone_label,
  zone_cluster_id = excluded.zone_cluster_id;

insert into public.expert_system_rules (
  rule_id,
  rule_name,
  condition_description,
  action_description,
  priority,
  is_active
)
values
  ('RULE_001', 'CRITICAL DRY EMERGENCY', 'soil_moisture < 20 AND temperature > 32', 'irrigation_decision = ON, water_requirement = 50L', 100, true),
  ('RULE_002', 'MODERATE DRY', 'soil_moisture BETWEEN 20 AND 40 AND humidity < 50', 'irrigation_decision = ON, water_requirement = 30L', 80, true),
  ('RULE_003', 'OPTIMAL CONDITIONS', 'soil_moisture > 60 AND humidity > 65', 'irrigation_decision = OFF', 40, true),
  ('RULE_004', 'HIGH TEMPERATURE COMPENSATION', 'temperature > 35 AND soil_moisture < 50', 'water_requirement += 15L', 70, true),
  ('RULE_005', 'NPK DEFICIENCY ALERT', 'nitrogen < 40 OR phosphorus < 30 OR potassium < 35', 'trigger LOW_NPK alert and soil amendment recommendation', 60, true)
on conflict (rule_id) do update
set
  rule_name = excluded.rule_name,
  condition_description = excluded.condition_description,
  action_description = excluded.action_description,
  priority = excluded.priority,
  is_active = excluded.is_active;
