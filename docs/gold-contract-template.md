# Gold Layer Data Contract

> Fill in this template before moving on to Day 2. One file per Gold
> release; check it in alongside the models it describes. The team that
> wrote Day 1 is the team that will read this on Day 2 morning, so write
> for a future-you who has slept since.

## Overview

_One paragraph: what does this Gold layer represent, who consumes it, and at
what cadence is it refreshed?_

---

## Tables

### `gold.<table_name>`

- **Grain:** _one row per ..._
- **Primary key:** `<column(s)>`
- **Refresh cadence:** _e.g. monthly, triggered by the `capstone_etl` DAG_
- **Owner:** _name + contact_

#### Columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `<col_1>` | `<type>` | _What it means and any units._ |
| `<col_2>` | `<type>` | |
| `<col_3>` | `<type>` | |

#### Tests

_List the dbt tests that protect this table (not_null, unique, accepted_values, custom)._

- `not_null` on `<col>`
- `unique` on `<pk>`
- ...

#### Known caveats

_Edge cases, known data-quality gaps, source-system quirks the consumer should be aware of._

---

## Versioning policy

_How will breaking changes be communicated? Suggested defaults:_

- **Additive changes** (new columns, new rows): no notice required.
- **Breaking changes** (removing or renaming columns, changing types or
  grain): announce at least one sprint in advance, ship behind a `_v2`
  table, and deprecate the old one with a fixed sunset date.

---

## Sign-off

The team accepts this contract as the basis for Day 2:

- Name: ____________________
- Date: ____________________
