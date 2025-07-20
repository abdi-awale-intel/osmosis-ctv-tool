function C = GetDataFromUber(datasource, query)
	warning('off','all');
	installpath = getenv('UBER_INSTALL_DIR');
    dllPath1 = fullfile(installpath,'bin','Intel.FabAuto.ESFW.DS.UBER.DataServiceFactory.dll');
    asm1 = NET.addAssembly(dllPath1);
    retval= Intel.FabAuto.ESFW.DS.UBER.MatlabUtil.GetDataFromUber(datasource,query,'F^j');
    C = csvimport(char(retval.filepath));
    if (retval.DelimiterPresent)
        [nRows,nCols] = size(C);
        for i=1:nRows 
            for j= 1: nCols
                C{i,j} =strrep(C{i,j},'F^j',',');
            end
        end
    end
	prevState = recycle('off'); % turn recycle off to permanently delete files
    delete(char(retval.filepath));
    recycle(prevState);
end