<?xml version="1.0" encoding="UTF-8"?>
<!--
    3b_resolve_to_tei.xsl

    Produces a resolved, single-reading TEI/XML version of the Lesefassung
    that matches exactly what was fed into the topic modelling - same
    content as 3_tei_to_text.xsl's plain-text output, but kept as valid
    TEI instead of being flattened, so it stays readable, citable, and
    directly re-usable (e.g. as the write-back target - see below).

    Same two content decisions as 3_tei_to_text.xsl, applied here to XML
    instead of plain text (verified empirically 2026-09-23 - see the
    comment in 3_tei_to_text.xsl for the counts):
      - <app> is resolved to a single reading: #W where both #A and #W
        survive, #A (or whichever single rdg exists) otherwise. The
        <app>/<rdg> wrapper itself is dropped - only the winning
        reading's content remains, in place, as ordinary running text.
      - <note> and <certainty> are removed entirely.
    Everything else (teiHeader, <p xml:id="P.n">, <milestone unit="sentence">,
    <persName>, <date>, etc.) is copied unchanged - unlike the plain-text
    step, there is no need to also unwrap inline elements like <persName>
    here: keeping them changes nothing about the text content BERTopic
    saw, and keeping the markup is strictly more useful in a citable
    XML artifact than flattening it would be.

    Run on lesefassung_milestones2.xml specifically (not a newer copy of
    the Lesefassung) - that is the file that was actually used to
    generate the text for the current topic model, and it has already
    been validated sentence-by-sentence against it (see verify_alignment.py
    in write_topics_to_tei/). Running this on a newer/different source
    would silently produce a file that does NOT match the NLP input any
    more.

    A nice side effect: once <app>/<note>/<certainty> are gone, the
    output's <milestone unit="sentence"/> stream is trivially 1:1 with
    the sentence list a topic model produces - no more app/rdg-aware
    text extraction needed to verify or consume it (contrast with the
    lengths verify_alignment.py had to go to against the un-resolved
    file). This file is a better write-back target than
    lesefassung_milestones2.xml going forward.

    NB: this is a derived NLP research-data artifact, not an alternative
    edition text - it deliberately discards apparatus and notes that the
    critical edition (Lesefassung) rightly keeps. Label/publish it as
    such (see the chat about freezing/documenting a specific text version
    for the topic-modelling workflow).
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="tei"
    version="2.0">

    <xsl:output method="xml" indent="no" encoding="UTF-8"/>

    <!-- Identity: copy everything unchanged by default -->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- Document the resolution as a plain XML comment right inside <TEI> -
         safe to insert anywhere (no schema content-model to violate),
         unlike trying to splice a <change> into <revisionDesc>. -->
    <xsl:template match="tei:TEI">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:comment> NLP-resolved version for topic modelling, generated <xsl:value-of
                select="format-date(current-date(), '[Y0001]-[M01]-[D01]')"/> by
                preprocessing/3b_resolve_to_tei.xsl from lesefassung_milestones2.xml.
                &lt;app&gt; resolved to &lt;rdg wit="#W"&gt; (or "#A" where "#W" is not
                attested); &lt;note&gt; and &lt;certainty&gt; removed. This is the text
                basis of the BERTopic run(s) - it is NOT the critical edition's reading
                text and must not be cited as such. </xsl:comment>
            <xsl:apply-templates select="node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- Resolve <app>: keep only the winning reading's content, drop the
         <app>/<rdg> wrapper itself so it reads as ordinary running text. -->
    <xsl:template match="tei:app">
        <xsl:choose>
            <xsl:when test="count(tei:rdg) = 1">
                <xsl:apply-templates select="tei:rdg/node()"/>
            </xsl:when>
            <xsl:when test="count(tei:rdg) = 2 and tei:rdg[@wit = '#W']">
                <xsl:apply-templates select="tei:rdg[@wit = '#W']/node()"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="tei:rdg[1]/node()"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Drop notes and certainty entirely -->
    <xsl:template match="tei:note | tei:certainty"/>

</xsl:stylesheet>
