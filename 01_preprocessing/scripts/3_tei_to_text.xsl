<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs tei"
    version="2.0">
    
    <xsl:strip-space elements="*"/>
    <xsl:output method="text" encoding="UTF-8" omit-xml-declaration="yes"/>
    
    <!-- Skip teiHeader -->
    <xsl:template match="tei:teiHeader"/>
    
    <!-- Paragraphs: emit content + delimiter -->
    <xsl:template match="//tei:p">
        <xsl:apply-templates/>
        <xsl:text>///</xsl:text>
    </xsl:template>
    
    <!-- Inline elements: keep content only -->
    <xsl:template match="tei:persName | tei:placeName | tei:bibl | tei:hi | tei:seg | tei:date">
        <xsl:apply-templates/>
    </xsl:template>
    
    <!-- Custom handling for <app> -->
    <xsl:template match="tei:app">
        <xsl:choose>
            <!-- Case 1: app has only one rdg (A or W) -->
            <xsl:when test="count(tei:rdg) = 1">
                <xsl:apply-templates select="tei:rdg"/>
            </xsl:when>
            
            <!-- Case 2: app has both A and W: take only W (base witness of the
                 Lesefassung, per its title statement; A is the printed Daumas/
                 Ulbrich 2013 edition and is used only where W does not survive -
                 see Case 3). Verified empirically 2026-09-23: of 3,676 <app>,
                 1,019 have both A and W, all resolved to W here; only 1,043 of
                 3,676 fall back to A because no W reading exists for that passage. -->
            <xsl:when test="count(tei:rdg) = 2 and tei:rdg[@wit='#W']">
                <xsl:apply-templates select="tei:rdg[@wit='#W']"/>
            </xsl:when>

            <!-- Case 3: otherwise (e.g. no #W): take first rdg if present -->
            <xsl:otherwise>
                <xsl:apply-templates select="tei:rdg[1]"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Render rdg content normally -->
    <xsl:template match="tei:rdg">
        <xsl:apply-templates/>
    </xsl:template>
    
    <!-- Replace milestone with delimiter -->
    <xsl:template match="tei:milestone[@unit = 'sentence']">
        <xsl:text>###</xsl:text>
    </xsl:template>
    
    <!-- Ignore notes and certainty -->
    <xsl:template match="tei:note | tei:certainty"/>
    
</xsl:stylesheet>
