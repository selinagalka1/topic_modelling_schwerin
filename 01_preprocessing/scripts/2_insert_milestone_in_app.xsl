<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="tei">
    
    <!-- Identity -->
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    
    <!-- Add milestone after <app> if ends with sentence punctuation and next starts capital -->
    <xsl:template match="tei:app">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
        
        <!-- gather text inside app -->
        <xsl:variable name="rawText"
            select="normalize-space(string-join(descendant::text(), ' '))"/>
        
        <!-- protect abbreviations (H., M., etc.) -->
        <xsl:variable name="abbr1"
            select="replace($rawText, '([A-Z])\.([A-Z])\.', '$1§DOT§$2§DOT§')"/>
        <xsl:variable name="abbr"
            select="replace($abbr1, '([A-Z])\.', '$1§DOT§')"/>
        <xsl:variable name="lastText"
            select="replace($abbr, '\s+$', '')"/>
        
        <!-- find next non-empty text node -->
        <xsl:variable name="nextText"
            select="normalize-space(
            (following-sibling::node()[self::text() and normalize-space(.)!=''])[1]
            )"/>
        
        <!-- skip if milestone already follows -->
        <xsl:variable name="nextMilestone"
            select="following-sibling::*[1][self::tei:milestone]"/>
        
        <!-- insert milestone if true sentence boundary -->
        <xsl:if
            test="not($nextMilestone)
            and matches($lastText, concat('[.!?…][”', '&quot;', &quot;']?$&quot;))
            and matches($nextText, '^[A-ZÀ-ÖØ-Ý]')
            and not(matches($lastText, '§DOT§$'))">
            <milestone unit='sentence'/>
        </xsl:if>
    </xsl:template>
    
</xsl:stylesheet>
