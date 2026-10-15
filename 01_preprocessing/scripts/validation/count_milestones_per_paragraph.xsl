<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:tei="http://www.tei-c.org/ns/1.0">
    
    <!-- Root template -->
    <xsl:template match="/">
        <paragraphs>
            <!-- Iterate over all paragraphs -->
            <xsl:for-each select="//tei:p">
                <paragraph id="{@xml:id}">
                    <milestoneCount>
                        <!-- Count milestones within the paragraph -->
                        <xsl:value-of select="count(.//tei:milestone[@unit = 'sentence'])"/>
                        
                    </milestoneCount>
                </paragraph>
            </xsl:for-each>
        </paragraphs>
    </xsl:template>
    
</xsl:stylesheet>
