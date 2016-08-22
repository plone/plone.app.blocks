Changelog
=========

1.0.1 (unreleased)
------------------

- Behavior shortname ``plone.draftable`` added.

- Fix code analysis errors.
  [gforcada]

1.0 (2016-03-28)
----------------

- Make sure draft is available before initializing the draft proxy object
  [vangheem]

1.0b3 (2015-06-10)
------------------

- Fix issue where drafting caused 'AttributeError: This object has no id'
  [datakurre]
- Fix issue where add forms with different content type but the context had conflicting draft
  [datakurre]

1.0b2 (2015-06-02)
------------------

- Fix rare issue where Dexterity draft had wrong portal_type
  [datakurre]

1.0b1 (2015-05-26)
------------------

- Add support for drafting on Dexterity add and edit forms
  when the drafting behavior is enabled for the content type
  [datakurre]

- Add autosave (using AJAX validation calls) support for
  Dexterity add and edit forms when drafting behavior is
  enabled for the content type
  [datakurre]

- Change to use UUIDs instead of intids
  [datakurre]

- Change Archetypes-support to be disabled by default
  [datakurre]

  Archetypes-support can included in zcml with::

      <include package="plone.app.drafts" file="archetypes.zcml" />


1.0a2 (2011-10-11)
------------------

- Added MANIFEST.in to fix our previous release. It was missing the history file.


1.0a1 (2011-10-10)
------------------

- Initial release.
