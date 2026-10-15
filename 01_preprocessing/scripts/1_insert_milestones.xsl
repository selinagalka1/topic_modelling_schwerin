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
    
    <!-- Paragraphs: start marker + sentence splitting; never inside note/certainty -->
    <xsl:template match="tei:p[not(ancestor::tei:note or ancestor::tei:certainty)]">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <milestone unit="sentence"/>
            <xsl:for-each select="node()">
                <xsl:choose>
                    <xsl:when test="self::text()">
                        <xsl:variable name="abbr1" select="replace(., '([A-Z])\.([A-Z])\.', '$1§DOT§$2§DOT§')"/>
                        <xsl:variable name="abbr"  select="replace($abbr1, '([A-Z])\.', '$1§DOT§')"/>
                        <xsl:call-template name="split-sentences">
                            <xsl:with-param name="text" select="$abbr"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="."/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </xsl:copy>
    </xsl:template>
    
    
    <!-- rdg: sentence splitting only if -->
    <!-- (a) it’s #A and parent <app> has 2 rdg, OR -->
    <!-- (b) parent <app> has only 1 rdg (any wit) -->
    <xsl:template match="tei:rdg[
        not(ancestor::tei:note or ancestor::tei:certainty)
        and (
        (matches(normalize-space(@wit),'(^|\s)#W(\s|$)') and count(../tei:rdg) = 2)
        or count(../tei:rdg) = 1
        )
        ]">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:for-each select="node()">
                <xsl:choose>
                    <xsl:when test="self::text()">
                        <xsl:variable name="abbr1" select="replace(., '([A-Z])\.([A-Z])\.', '$1§DOT§$2§DOT§')"/>
                        <xsl:variable name="abbr"  select="replace($abbr1, '([A-Z])\.', '$1§DOT§')"/>
                        <xsl:call-template name="split-sentences">
                            <xsl:with-param name="text" select="$abbr"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="."/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </xsl:copy>
    </xsl:template>
    
    <!-- all other rdg: pass through unchanged -->
    <xsl:template match="tei:rdg">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    
    
    <!-- Sentence splitter -->
    <xsl:template name="split-sentences">
        <xsl:param name="text"/>
        <xsl:analyze-string select="$text" regex="([.!?])(\s|&#xA0;)">
            <xsl:matching-substring>
                <xsl:value-of select="regex-group(1)"/>
                <milestone unit="sentence"/>
                <xsl:value-of select="regex-group(2)"/>
            </xsl:matching-substring>
            <xsl:non-matching-substring>
                <xsl:value-of select="replace(., '§DOT§', '.')"/>
            </xsl:non-matching-substring>
        </xsl:analyze-string>
    </xsl:template>
    
</xsl:stylesheet>
