create table adwords_en_us (
    keyword text primary key,
    keyword_tsv tsvector generated always as ( to_tsvector('english', keyword)) stored,
    volume int not null,
    cpc float default  0.0,
    competition float default  0.0,
    spell_type varchar(32)
);

create index adwords_en_us_keyword_tsv_idx on adwords_en_us using gin(keyword_tsv);
create index adwords_en_us_spell_type_volume_idx on adwords_en_us (spell_type, volume desc);
