# Submission Intake Runbook

## Purpose

This runbook defines the fallback for brethren without GitHub write access.

## Canonical Path

For each mission:

```
missions/<MISSION_ID>/submissions/
  mr-gold.txt
  blue-0.txt
  sienna-4.txt
```

## Temporary Intake Path

Recommended:

```
Alvorada/inbox/<MISSION_ID>/
```

This may exist in:

- local storage;
- OneDrive;
- SharePoint.

Temporary intake storage is not canonical.

## Required File Header

Use exactly:

```
MISSION_ID: <MISSION_ID>
MEMBER: <MEMBER_DESIGNATION>
RECEIVED_AT: <ISO-8601 timestamp>
SOURCE_ENVIRONMENT: <environment>
STATUS: SUBMITTED_FOR_COLLECTION
EDITED_AFTER_RECEIPT: NO
```

## Intake Rules

- preserve the submission verbatim;
- use UTF-8 plain text;
- one member per file;
- no combined submission files;
- no cleanup before adjudication;
- no synthesis while collection is OPEN;
- no replacement of prior versions;
- supersede with a new file if correction is required;
- record who performed the import;
- do not store secrets, tokens, system prompts, or unrelated chat history.

## File Naming

Canonical names:

```
mr-gold.txt
blue-0.txt
sienna-4.txt
```

Correction files:

```
mr-gold.v2.txt
blue-0.v2.txt
sienna-4.v2.txt
```

Do not overwrite the original file.

## Collection Update

After import:

- add the member to received;
- remove the member from missing;
- leave status OPEN until André closes collection.

## Adjudication Boundary

- imported files are evidence;
- adjudication is separate;
- adjudication must not modify the original submission files.
