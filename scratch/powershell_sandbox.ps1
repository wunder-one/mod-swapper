
#        "/MIR",   # mirror
#        "/FFT",   # use FAT file times (2-second tolerance, more reliable)
#        "/Z",     # restartable mode in case of interruption
#        "/NP",    # no progress percentage in output


# Folder name pattern: PASS
robocopy "C:\Users\wes\Desktop\test-source\Baldurs Gate 3" "C:\Users\wes\Desktop\test-dest\Baldurs Gate 3" /XF *.exe *.dll *.log /XD Engine Game Localization /MIR /FFT /Z /NP

# Folder name pattern: PASS
robocopy "C:\Users\wes\Desktop\test-dest\Baldurs Gate 3" "C:\Users\wes\Desktop\test-source\Baldurs Gate 3" /XF *.exe *.dll *.log /XD Engine Game Localization /MIR /FFT /Z /NP

# Relative path pattern: FAIL

# Full path pattern: PASS
robocopy "C:\Users\wes\Desktop\test-source\Baldurs Gate 3" "C:\Users\wes\Desktop\test-dest\Baldurs Gate 3" /XF *.exe *.dll *.log /XD "C:\Users\wes\Desktop\test-source\Baldurs Gate 3\Data\Generated\Public\Engine" "C:\Users\wes\Desktop\test-source\Baldurs Gate 3\Data\Generated\Public\Game" Localization /MIR /FFT /Z /NP

# Full path pattern: PASS
robocopy "C:\Users\wes\Desktop\test-dest\Baldurs Gate 3" "C:\Users\wes\Desktop\test-source\Baldurs Gate 3" /XF *.exe *.dll *.log /XD "C:\Users\wes\Desktop\test-source\Baldurs Gate 3\Data\Generated\Public\Engine" "C:\Users\wes\Desktop\test-source\Baldurs Gate 3\Data\Generated\Public\Game" Localization /MIR /FFT /Z /NP